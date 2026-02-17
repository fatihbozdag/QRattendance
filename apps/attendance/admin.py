import csv
import datetime

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .importers import import_students_to_course, parse_ubys_student_list
from .models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseMaterial,
    Enrollment,
    ExcusedAbsence,
    Holiday,
    Schedule,
    Student,
)


# --- Resources for import/export ---

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = ("student_id", "name", "email")
        import_id_fields = ("student_id",)


class AttendanceRecordResource(resources.ModelResource):
    class Meta:
        model = AttendanceRecord
        fields = (
            "session__course__code",
            "session__date",
            "session__week_number",
            "student_id_entered",
            "ip_address",
            "timestamp",
        )


# --- Inlines ---

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    autocomplete_fields = ["student"]
    fields = ["student"]


class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 0
    fields = ["title", "description", "file", "url", "order"]


class ScheduleForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TextInput(attrs={"placeholder": "HH:MM", "size": "5"}),
        input_formats=["%H:%M"],
    )
    end_time = forms.TimeField(
        widget=forms.TextInput(attrs={"placeholder": "HH:MM", "size": "5"}),
        input_formats=["%H:%M"],
    )

    class Meta:
        model = Schedule
        fields = "__all__"


class ScheduleInline(admin.TabularInline):
    model = Schedule
    form = ScheduleForm
    extra = 1


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    readonly_fields = ["student_id_entered", "student", "ip_address", "user_agent", "timestamp"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ExcusedAbsenceInline(admin.TabularInline):
    model = ExcusedAbsence
    extra = 0
    autocomplete_fields = ["student"]


# --- Admin classes ---

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ["student_id", "name", "email"]
    search_fields = ["student_id", "name", "email"]
    list_filter = ["enrollments__course"]


class CourseAdminForm(forms.ModelForm):
    student_list_file = forms.FileField(
        required=False,
        label="UBYS Student List (.xls)",
        help_text="Upload the UBYS attendance .xls file to import students and create enrollments.",
    )

    class Meta:
        model = Course
        fields = "__all__"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = ["code", "name", "semester", "course_hours", "qr_token", "total_weeks", "qr_code_link", "matrix_link", "import_grades_link", "dashboard_link"]
    search_fields = ["code", "name"]
    list_filter = ["semester"]
    readonly_fields = ["qr_token", "slug"]
    inlines = [ScheduleInline, EnrollmentInline, CourseMaterialInline]
    actions = ["export_attendance_matrix"]

    fieldsets = (
        ("Course Info", {
            "fields": ("code", "name", "semester", "lecturer", "course_hours"),
        }),
        ("Schedule Config", {
            "fields": ("semester_start_date", "total_weeks"),
        }),
        ("Student Import", {
            "fields": ("student_list_file",),
            "description": "Upload a UBYS .xls file to bulk-import students into this course.",
        }),
        ("Auto Fields", {
            "fields": ("qr_token", "slug"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="QR Code")
    def qr_code_link(self, obj):
        url = reverse("course_qr_code", args=[obj.pk])
        return format_html('<a href="{}">QR Code</a>', url)

    @admin.display(description="Attendance")
    def matrix_link(self, obj):
        url = reverse("attendance_matrix", args=[obj.pk])
        return format_html('<a href="{}">View Matrix</a>', url)

    @admin.display(description="Grades")
    def import_grades_link(self, obj):
        url = reverse("import_grades", args=[obj.pk])
        return format_html('<a href="{}">Import Grades</a>', url)

    @admin.display(description="Dashboard")
    def dashboard_link(self, obj):
        url = reverse("instructor_dashboard", args=[obj.pk])
        return format_html('<a href="{}">Dashboard</a>', url)

    @admin.action(description="Export attendance matrix (CSV)")
    def export_attendance_matrix(self, request, queryset):
        if queryset.count() != 1:
            messages.warning(request, "Please select exactly one course to export.")
            return
        course = queryset.first()

        sessions = ClassSession.objects.filter(
            course=course, is_cancelled=False
        ).order_by("date", "start_time")
        enrollments = Enrollment.objects.filter(course=course).select_related("student")

        # Build set of (student_pk, session_pk) each student attended
        attended = set(
            AttendanceRecord.objects.filter(
                session__course=course, session__is_cancelled=False, student__isnull=False
            ).values_list("student_id", "session_id")
        )

        # Build set of (student_pk, session_pk) for excused absences
        excused = set(
            ExcusedAbsence.objects.filter(
                session__course=course, session__is_cancelled=False
            ).values_list("student_id", "session_id")
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{course.code}_attendance.csv"'
        writer = csv.writer(response)

        # Header: Student ID, Name, date columns..., Total, %
        header = ["Student ID", "Name"]
        for s in sessions:
            header.append(f"W{s.week_number} {s.date.strftime('%m/%d')}")
        header += ["Attended", "Total", "Excused", "%"]
        writer.writerow(header)

        total_sessions = sessions.count()
        for enrollment in enrollments:
            student = enrollment.student
            row = [student.student_id, student.name]
            student_attended = 0
            student_excused = 0
            for s in sessions:
                if (student.pk, s.pk) in excused:
                    row.append("E")
                    student_excused += 1
                elif (student.pk, s.pk) in attended:
                    row.append("P")
                    student_attended += 1
                else:
                    row.append("A")
            effective_total = total_sessions - student_excused
            pct = round(student_attended / effective_total * 100) if effective_total > 0 else 0
            row += [student_attended, total_sessions, student_excused, f"{pct}%"]
            writer.writerow(row)

        return response

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # --- Student import from uploaded file ---
        uploaded_file = form.cleaned_data.get("student_list_file")
        if uploaded_file:
            try:
                students = parse_ubys_student_list(uploaded_file)
                created_students, created_enrollments = import_students_to_course(obj, students)
                messages.success(
                    request,
                    f"Imported {len(students)} students: "
                    f"{created_students} new students, {created_enrollments} new enrollments.",
                )
            except Exception as e:
                messages.error(request, f"Student import failed: {e}")

        # --- Auto-generate ClassSessions ---
        if obj.semester_start_date:
            schedules = obj.schedules.all()
            if schedules.exists():
                holiday_dates = set(Holiday.objects.values_list("date", flat=True))
                session_count = 0
                skipped = 0
                for schedule in schedules:
                    for week in range(obj.total_weeks):
                        # Find the date for this schedule's day_of_week in the given week
                        week_start = obj.semester_start_date + datetime.timedelta(weeks=week)
                        # semester_start_date weekday vs schedule day_of_week
                        days_ahead = schedule.day_of_week - week_start.weekday()
                        if days_ahead < 0:
                            days_ahead += 7
                        session_date = week_start + datetime.timedelta(days=days_ahead)

                        if session_date in holiday_dates:
                            skipped += 1
                            continue

                        _, created = ClassSession.objects.get_or_create(
                            course=obj,
                            date=session_date,
                            start_time=schedule.start_time,
                            defaults={
                                "end_time": schedule.end_time,
                                "week_number": week + 1,
                            },
                        )
                        if created:
                            session_count += 1

                parts = []
                if session_count:
                    parts.append(f"Generated {session_count} class sessions for {obj.total_weeks} weeks.")
                if skipped:
                    parts.append(f"Skipped {skipped} session(s) on holidays.")
                if parts:
                    messages.success(request, " ".join(parts))


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ["date", "name"]
    ordering = ["date"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cancelled = ClassSession.objects.filter(date=obj.date, is_cancelled=False).update(is_cancelled=True)
        if cancelled:
            messages.info(request, f"Auto-cancelled {cancelled} session(s) on {obj.date} ({obj.name}).")

    def delete_model(self, request, obj):
        restored = ClassSession.objects.filter(date=obj.date, is_cancelled=True).update(is_cancelled=False)
        super().delete_model(request, obj)
        if restored:
            messages.info(request, f"Restored {restored} session(s) on {obj.date}.")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "midterm_grade", "final_grade"]
    list_filter = ["course"]
    list_editable = ["midterm_grade", "final_grade"]
    autocomplete_fields = ["student", "course"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["course", "day_of_week", "start_time", "end_time", "grace_before_minutes", "grace_after_minutes"]
    list_filter = ["course", "day_of_week"]


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ["course", "date", "week_number", "start_time", "end_time", "is_cancelled", "attendance_count"]
    list_filter = ["course", "is_cancelled", "date"]
    search_fields = ["course__code", "course__name"]
    inlines = [AttendanceRecordInline, ExcusedAbsenceInline]
    actions = ["export_attendance_csv"]

    @admin.action(description="Export attendance CSV for selected sessions")
    def export_attendance_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
        writer = csv.writer(response)
        writer.writerow(["Course", "Date", "Week", "Student ID", "IP Address", "Timestamp"])
        for session in queryset.select_related("course").prefetch_related("records"):
            for record in session.records.all():
                writer.writerow([
                    session.course.code,
                    session.date,
                    session.week_number,
                    record.student_id_entered,
                    record.ip_address,
                    record.timestamp,
                ])
        return response


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(ImportExportModelAdmin):
    resource_class = AttendanceRecordResource
    list_display = ["student_id_entered", "session", "ip_address", "timestamp"]
    list_filter = ["session__course", "session__date"]
    search_fields = ["student_id_entered"]
    readonly_fields = ["ip_address", "user_agent", "timestamp"]


@admin.register(ExcusedAbsence)
class ExcusedAbsenceAdmin(admin.ModelAdmin):
    list_display = ["student", "session", "reason", "created_at"]
    list_filter = ["session__course", "session__date"]
    search_fields = ["student__student_id", "student__name", "reason"]
    autocomplete_fields = ["student", "session"]

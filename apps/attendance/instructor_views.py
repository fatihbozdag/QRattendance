import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import AttendanceRecord, ClassSession, Course, CourseMaterial, Enrollment, ExcusedAbsence


def _course_context(course, view_name):
    """Common context for all course-level instructor views."""
    return {"course": course, "view_name": view_name}


@staff_member_required(login_url="/accounts/login/")
def instructor_course_list(request):
    """List all courses with student counts."""
    courses = Course.objects.annotate(
        student_count=Count("enrollments", distinct=True),
        session_count=Count("sessions", filter=Q(sessions__is_cancelled=False), distinct=True),
    ).order_by("-semester", "code")
    return render(request, "instructor/course_list.html", {
        "courses": courses,
        "view_name": "course_list",
    })


@staff_member_required(login_url="/accounts/login/")
def instructor_course_dashboard(request, course_id):
    """Instructor dashboard with summary, at-risk students, and quick actions."""
    course = get_object_or_404(Course, pk=course_id)

    sessions = ClassSession.objects.filter(course=course, is_cancelled=False)
    total_sessions = sessions.count()
    enrollments = Enrollment.objects.filter(course=course).select_related("student")
    total_students = enrollments.count()

    attendance_records = set(
        AttendanceRecord.objects.filter(
            session__course=course, session__is_cancelled=False, student__isnull=False
        ).values_list("student_id", "session_id")
    )
    excused_records = set(
        ExcusedAbsence.objects.filter(
            session__course=course, session__is_cancelled=False
        ).values_list("student_id", "session_id")
    )

    student_stats = []
    total_pct_sum = 0
    for enrollment in enrollments:
        student = enrollment.student
        attended = sum(1 for s in sessions if (student.pk, s.pk) in attendance_records)
        excused = sum(1 for s in sessions if (student.pk, s.pk) in excused_records)
        effective = total_sessions - excused
        pct = round(attended / effective * 100) if effective > 0 else 0
        total_pct_sum += pct
        student_stats.append({
            "student": student,
            "attended": attended,
            "excused": excused,
            "effective_total": effective,
            "percentage": pct,
        })

    avg_attendance = round(total_pct_sum / total_students) if total_students > 0 else 0
    at_risk = sorted(
        [s for s in student_stats if s["percentage"] < 60],
        key=lambda x: x["percentage"],
    )

    ctx = _course_context(course, "dashboard")
    ctx.update({
        "total_students": total_students,
        "total_sessions": total_sessions,
        "avg_attendance": avg_attendance,
        "at_risk": at_risk,
    })
    return render(request, "instructor/dashboard.html", ctx)


@staff_member_required(login_url="/accounts/login/")
def instructor_attendance_matrix(request, course_id):
    """Show attendance matrix: students x sessions."""
    course = get_object_or_404(Course, pk=course_id)
    sessions = ClassSession.objects.filter(course=course, is_cancelled=False).order_by("date", "start_time")
    enrollments = Enrollment.objects.filter(course=course).select_related("student").order_by("student__student_id")

    records = AttendanceRecord.objects.filter(session__in=sessions).values_list(
        "student_id_entered", "session_id"
    )
    attendance_set = {(sid, sess_id) for sid, sess_id in records}

    excused_set = set(
        ExcusedAbsence.objects.filter(
            session__in=sessions
        ).values_list("student_id", "session_id")
    )

    rows = []
    for enrollment in enrollments:
        student = enrollment.student
        attendance = []
        for session in sessions:
            if (student.pk, session.pk) in excused_set:
                attendance.append("E")
            elif (student.student_id, session.id) in attendance_set:
                attendance.append("P")
            else:
                attendance.append("A")
        rows.append({
            "student": student,
            "attendance": attendance,
            "total": sum(1 for a in attendance if a == "P"),
        })

    export = request.GET.get("export")
    if export == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{course.code}_attendance.csv"'
        writer = csv.writer(response)
        header = ["Student ID", "Name"] + [f"W{s.week_number} ({s.date})" for s in sessions] + ["Total"]
        writer.writerow(header)
        for row in rows:
            writer.writerow(
                [row["student"].student_id, row["student"].name]
                + row["attendance"]
                + [row["total"]]
            )
        return response

    ctx = _course_context(course, "matrix")
    ctx.update({"sessions": sessions, "rows": rows})
    return render(request, "instructor/attendance_matrix.html", ctx)


@staff_member_required(login_url="/accounts/login/")
def instructor_qr_code(request, course_id):
    """Display a printable QR code page for a course."""
    course = get_object_or_404(Course, pk=course_id)
    scan_url = request.build_absolute_uri(f"/a/{course.qr_token}/")
    ctx = _course_context(course, "qr")
    ctx["scan_url"] = scan_url
    return render(request, "instructor/qr_code.html", ctx)


@staff_member_required(login_url="/accounts/login/")
def instructor_import_grades(request, course_id):
    """Upload CSV to bulk-update midterm/final grades for a course."""
    course = get_object_or_404(Course, pk=course_id)
    results = None

    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        decoded = csv_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        updated = 0
        skipped = []
        errors = []

        for i, row in enumerate(reader, start=2):
            student_id = row.get("student_id", "").strip()
            if not student_id:
                errors.append(f"Row {i}: missing student_id")
                continue

            try:
                enrollment = Enrollment.objects.get(student__student_id=student_id, course=course)
            except Enrollment.DoesNotExist:
                skipped.append(student_id)
                continue

            changed = False
            for field in ("midterm", "final"):
                val = row.get(field, "").strip()
                if val:
                    try:
                        grade = Decimal(val)
                    except InvalidOperation:
                        errors.append(f"Row {i}: invalid {field} value '{val}'")
                        continue
                    setattr(enrollment, f"{field}_grade", grade)
                    changed = True

            if changed:
                enrollment.save()
                updated += 1

        results = {
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
        }

    ctx = _course_context(course, "grades")
    ctx["results"] = results
    return render(request, "instructor/import_grades.html", ctx)


@staff_member_required(login_url="/accounts/login/")
def instructor_materials(request, course_id):
    """Manage course materials: list, add, and delete."""
    course = get_object_or_404(Course, pk=course_id)
    error = None
    success = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            title = request.POST.get("title", "").strip()
            description = request.POST.get("description", "").strip()
            url = request.POST.get("url", "").strip()
            file = request.FILES.get("file")

            if not title:
                error = "Title is required."
            elif not url and not file:
                error = "Please provide either a URL or a file."
            else:
                material = CourseMaterial(
                    course=course,
                    title=title,
                    description=description,
                    url=url,
                )
                if file:
                    material.file = file
                material.save()
                success = f'Material "{title}" added.'

        elif action == "delete":
            material_id = request.POST.get("material_id")
            deleted = CourseMaterial.objects.filter(pk=material_id, course=course).delete()
            if deleted[0]:
                success = "Material deleted."

    materials = course.materials.all()
    ctx = _course_context(course, "materials")
    ctx.update({"materials": materials, "error": error, "success": success})
    return render(request, "instructor/materials.html", ctx)

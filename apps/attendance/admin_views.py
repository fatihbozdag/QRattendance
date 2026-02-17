import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import AttendanceRecord, ClassSession, Course, Enrollment, ExcusedAbsence


@staff_member_required
def course_qr_code(request, course_id):
    """Display a printable QR code page for a course."""
    course = get_object_or_404(Course, pk=course_id)
    scan_url = request.build_absolute_uri(f"/a/{course.qr_token}/")
    return render(request, "admin/course_qr_code.html", {
        "course": course,
        "scan_url": scan_url,
    })


@staff_member_required
def attendance_matrix(request, course_id):
    """Show attendance matrix: students x sessions."""
    course = get_object_or_404(Course, pk=course_id)
    sessions = ClassSession.objects.filter(course=course, is_cancelled=False).order_by("date", "start_time")
    enrollments = Enrollment.objects.filter(course=course).select_related("student").order_by("student__student_id")

    # Build matrix
    records = AttendanceRecord.objects.filter(session__in=sessions).values_list(
        "student_id_entered", "session_id"
    )
    attendance_set = {(sid, sess_id) for sid, sess_id in records}

    # Excused absences: (student_pk, session_pk)
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
        row = {
            "student": student,
            "attendance": attendance,
            "total": sum(1 for a in attendance if a == "P"),
        }
        rows.append(row)

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

    return render(request, "admin/attendance_matrix.html", {
        "course": course,
        "sessions": sessions,
        "rows": rows,
    })


@staff_member_required
def import_grades(request, course_id):
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

        for i, row in enumerate(reader, start=2):  # row 1 is header
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

    return render(request, "admin/import_grades.html", {
        "course": course,
        "results": results,
    })


@staff_member_required
def instructor_dashboard(request, course_id):
    """Instructor dashboard with summary, at-risk students, and quick actions."""
    course = get_object_or_404(Course, pk=course_id)

    sessions = ClassSession.objects.filter(course=course, is_cancelled=False)
    total_sessions = sessions.count()
    enrollments = Enrollment.objects.filter(course=course).select_related("student")
    total_students = enrollments.count()

    # Build attendance data per student
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

    return render(request, "admin/instructor_dashboard.html", {
        "course": course,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "avg_attendance": avg_attendance,
        "at_risk": at_risk,
    })

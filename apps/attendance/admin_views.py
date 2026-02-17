import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import AttendanceRecord, ClassSession, Course, Enrollment


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

    rows = []
    for enrollment in enrollments:
        student = enrollment.student
        row = {
            "student": student,
            "attendance": [
                (student.student_id, session.id) in attendance_set
                for session in sessions
            ],
        }
        row["total"] = sum(row["attendance"])
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
                + ["P" if a else "A" for a in row["attendance"]]
                + [row["total"]]
            )
        return response

    return render(request, "admin/attendance_matrix.html", {
        "course": course,
        "sessions": sessions,
        "rows": rows,
    })

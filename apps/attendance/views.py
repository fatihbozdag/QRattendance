from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from apps.core.utils import get_client_ip

from .models import AttendanceRecord, Course, Student
from .services import get_active_session, get_next_session_info


@require_GET
def scan_landing(request, qr_token):
    """Landing page when student scans QR code."""
    course = get_object_or_404(Course, qr_token=qr_token)
    session, schedule = get_active_session(course)

    if session is None:
        next_schedule = get_next_session_info(course)
        return render(request, "attendance/not_active.html", {
            "course": course,
            "next_schedule": next_schedule,
        })

    return render(request, "attendance/form.html", {
        "course": course,
        "session": session,
    })


@require_POST
def submit_attendance(request, qr_token):
    """Process attendance submission."""
    course = get_object_or_404(Course, qr_token=qr_token)
    session, schedule = get_active_session(course)

    if session is None:
        return render(request, "attendance/not_active.html", {
            "course": course,
            "next_schedule": get_next_session_info(course),
        })

    student_id = request.POST.get("student_id", "").strip()
    if not student_id:
        return render(request, "attendance/form.html", {
            "course": course,
            "session": session,
            "error": "Please enter your student ID.",
        })

    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    # Check IP uniqueness for this session
    if AttendanceRecord.objects.filter(session=session, ip_address=ip_address).exists():
        return render(request, "attendance/error.html", {
            "course": course,
            "message": "Attendance already recorded from this device.",
        })

    # Check student ID uniqueness for this session
    if AttendanceRecord.objects.filter(session=session, student_id_entered=student_id).exists():
        return render(request, "attendance/error.html", {
            "course": course,
            "message": "This student ID has already been recorded for this session.",
        })

    # Try to link to a known student
    student = Student.objects.filter(student_id=student_id).first()

    AttendanceRecord.objects.create(
        session=session,
        student=student,
        student_id_entered=student_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return render(request, "attendance/success.html", {
        "course": course,
        "student_id": student_id,
        "student_name": student.name if student else None,
    })

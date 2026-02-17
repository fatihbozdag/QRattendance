from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.attendance.models import ClassSession, Enrollment, Student

from .decorators import portal_login_required
from .services import (
    get_logged_in_student_id,
    login_student,
    logout_student,
    mask_email,
    send_magic_link,
    validate_email_domain,
    verify_token,
)


@require_GET
def request_link(request):
    if get_logged_in_student_id(request):
        return redirect("portal:dashboard")
    return render(request, "portal/request_link.html")


@require_POST
def request_link_submit(request):
    student_id = request.POST.get("student_id", "").strip()
    if not student_id:
        return render(request, "portal/request_link.html", {"error": "Please enter your student ID."})

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return render(request, "portal/request_link.html", {"error": "Student ID not found."})

    if not student.email or not validate_email_domain(student.email):
        request.session["portal_register_student_id"] = student.student_id
        return redirect("portal:register")

    send_magic_link(request, student)
    return render(request, "portal/check_email.html", {"masked_email": mask_email(student.email)})


@require_GET
def register(request):
    student_id = request.session.get("portal_register_student_id")
    if not student_id:
        return redirect("portal:request_link")
    return render(request, "portal/register.html", {"student_id": student_id})


@require_POST
def register_submit(request):
    student_id = request.session.get("portal_register_student_id")
    if not student_id:
        return redirect("portal:request_link")

    email = request.POST.get("email", "").strip()
    if not email:
        return render(request, "portal/register.html", {"student_id": student_id, "error": "Please enter your email."})

    if not validate_email_domain(email):
        return render(request, "portal/register.html", {"student_id": student_id, "error": "Only .edu.tr email addresses are allowed."})

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return redirect("portal:request_link")

    student.email = email
    student.save(update_fields=["email"])
    request.session.pop("portal_register_student_id", None)

    send_magic_link(request, student)
    return render(request, "portal/check_email.html", {"masked_email": mask_email(student.email)})


@require_GET
def magic_login(request, token):
    student_id = verify_token(token)
    if not student_id:
        return render(request, "portal/login_invalid.html")

    login_student(request, student_id)
    return redirect("portal:dashboard")


@require_GET
@portal_login_required
def dashboard(request):
    student_id = get_logged_in_student_id(request)
    student = get_object_or_404(Student, student_id=student_id)
    enrollments = Enrollment.objects.filter(student=student).select_related("course")

    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        total_sessions = ClassSession.objects.filter(course=course, is_cancelled=False).count()
        attended = ClassSession.objects.filter(
            course=course,
            is_cancelled=False,
            records__student=student,
        ).distinct().count()
        percentage = round(attended / total_sessions * 100) if total_sessions > 0 else 0
        courses.append({
            "name": course.name,
            "code": course.code,
            "attended": attended,
            "total": total_sessions,
            "percentage": percentage,
        })

    return render(request, "portal/dashboard.html", {"student": student, "courses": courses})


@require_GET
def portal_logout(request):
    logout_student(request)
    return redirect("portal:request_link")

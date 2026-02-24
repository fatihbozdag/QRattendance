from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.attendance.models import ClassSession, CourseMaterial, Enrollment, ExcusedAbsence, Student

ATTENDANCE_THRESHOLD = 60  # minimum attendance percentage

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
    email = request.POST.get("email", "").strip().lower()
    if not email:
        return render(request, "portal/request_link.html", {"error": "Lutfen e-posta adresinizi girin."})

    if not validate_email_domain(email):
        return render(request, "portal/request_link.html", {"error": "Sadece .edu.tr uzantili e-posta adresleri kabul edilir."})

    # Try finding student by email first
    student = Student.objects.filter(email=email).first()

    # If not found, extract student_id from email local part (e.g. 2021123456@ogr.oku.edu.tr)
    if not student:
        local_part = email.rsplit("@", 1)[0]
        try:
            student = Student.objects.get(student_id=local_part)
        except Student.DoesNotExist:
            return render(request, "portal/request_link.html", {"error": "Bu e-posta adresiyle eslesen ogrenci bulunamadi."})
        # Save the email for future logins
        student.email = email
        student.save(update_fields=["email"])

    if send_magic_link(request, student):
        return render(request, "portal/check_email.html", {"masked_email": mask_email(student.email)})
    return render(request, "portal/request_link.html", {"error": "E-posta gonderilemedi. Lutfen daha sonra tekrar deneyin."})


@require_GET
def register(request):
    email = request.session.get("portal_register_email")
    if not email:
        return redirect("portal:request_link")
    return render(request, "portal/register.html", {"email": email})


@require_POST
def register_submit(request):
    email = request.session.get("portal_register_email")
    if not email:
        return redirect("portal:request_link")

    student_id = request.POST.get("student_id", "").strip()
    if not student_id:
        return render(request, "portal/register.html", {"email": email, "error": "Lutfen ogrenci numaranizi girin."})

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return render(request, "portal/register.html", {"email": email, "error": "Ogrenci numarasi bulunamadi."})

    student.email = email
    student.save(update_fields=["email"])
    request.session.pop("portal_register_email", None)

    if send_magic_link(request, student):
        return render(request, "portal/check_email.html", {"masked_email": mask_email(student.email)})
    return render(request, "portal/register.html", {"email": email, "error": "E-posta gonderilemedi. Lutfen daha sonra tekrar deneyin."})


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
        excused_count = ExcusedAbsence.objects.filter(
            student=student, session__course=course, session__is_cancelled=False
        ).count()
        effective_total = total_sessions - excused_count
        percentage = round(attended / effective_total * 100) if effective_total > 0 else 0
        courses.append({
            "id": course.pk,
            "name": course.name,
            "code": course.code,
            "attended": attended,
            "total": total_sessions,
            "excused": excused_count,
            "effective_total": effective_total,
            "percentage": percentage,
            "below_threshold": percentage < ATTENDANCE_THRESHOLD,
        })

    return render(request, "portal/dashboard.html", {
        "student": student,
        "courses": courses,
        "threshold": ATTENDANCE_THRESHOLD,
    })


@require_GET
@portal_login_required
def course_detail(request, course_id):
    student_id = get_logged_in_student_id(request)
    student = get_object_or_404(Student, student_id=student_id)
    enrollment = get_object_or_404(Enrollment, student=student, course_id=course_id)
    course = enrollment.course

    # Attendance detail
    sessions = ClassSession.objects.filter(
        course=course, is_cancelled=False
    ).order_by("date", "start_time")

    attended_session_ids = set(
        ClassSession.objects.filter(
            course=course,
            is_cancelled=False,
            records__student=student,
        ).values_list("id", flat=True)
    )

    excused_session_ids = set(
        ExcusedAbsence.objects.filter(
            student=student, session__course=course, session__is_cancelled=False
        ).values_list("session_id", flat=True)
    )

    session_list = []
    for s in sessions:
        session_list.append({
            "date": s.date,
            "week_number": s.week_number,
            "attended": s.id in attended_session_ids,
            "excused": s.id in excused_session_ids,
        })

    total = len(session_list)
    attended_count = len(attended_session_ids)
    excused_count = len(excused_session_ids)
    effective_total = total - excused_count
    percentage = round(attended_count / effective_total * 100) if effective_total > 0 else 0

    # Materials
    materials = CourseMaterial.objects.filter(course=course)

    # Grades
    midterm = enrollment.midterm_grade
    final = enrollment.final_grade

    return render(request, "portal/course_detail.html", {
        "student": student,
        "course": course,
        "sessions": session_list,
        "attended_count": attended_count,
        "total_sessions": total,
        "excused_count": excused_count,
        "effective_total": effective_total,
        "percentage": percentage,
        "below_threshold": percentage < ATTENDANCE_THRESHOLD,
        "threshold": ATTENDANCE_THRESHOLD,
        "materials": materials,
        "midterm": midterm,
        "final": final,
    })


@require_GET
def portal_logout(request):
    logout_student(request)
    return redirect("portal:request_link")

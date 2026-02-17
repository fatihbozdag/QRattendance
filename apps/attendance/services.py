from datetime import datetime, timedelta

from django.utils import timezone

from .models import ClassSession, Schedule


def get_active_session(course):
    """
    Check if a class is currently in session for the given course.
    Returns (ClassSession, Schedule) if active, (None, None) otherwise.
    Also returns the next upcoming schedule if not active.
    """
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()
    current_day = now.weekday()

    schedules = Schedule.objects.filter(course=course, day_of_week=current_day)

    for schedule in schedules:
        # Calculate effective window with grace periods using datetime for safe arithmetic
        effective_start_dt = datetime.combine(today, schedule.start_time) - timedelta(minutes=schedule.grace_before_minutes)
        effective_end_dt = datetime.combine(today, schedule.end_time) + timedelta(minutes=schedule.grace_after_minutes)
        now_dt = datetime.combine(today, current_time)

        if effective_start_dt <= now_dt <= effective_end_dt:
            # Class is active — get or create session
            session, _ = ClassSession.objects.get_or_create(
                course=course,
                date=today,
                start_time=schedule.start_time,
                defaults={
                    "end_time": schedule.end_time,
                    "week_number": _calculate_week_number(course, today),
                },
            )
            if session.is_cancelled:
                return None, schedule
            return session, schedule

    return None, None


def get_next_session_info(course):
    """Get info about the next upcoming scheduled class."""
    now = timezone.localtime()
    current_day = now.weekday()
    current_time = now.time()

    schedules = list(Schedule.objects.filter(course=course).order_by("day_of_week", "start_time"))
    if not schedules:
        return None

    # Find next schedule after now
    for schedule in schedules:
        if schedule.day_of_week > current_day or (
            schedule.day_of_week == current_day and schedule.start_time > current_time
        ):
            return schedule

    # Wrap around to first schedule of next week
    return schedules[0] if schedules else None


def _calculate_week_number(course, date):
    """Calculate week number based on earliest session or default to 1."""
    earliest = ClassSession.objects.filter(course=course).order_by("date").first()
    if earliest:
        delta = (date - earliest.date).days
        return (delta // 7) + 1
    return 1

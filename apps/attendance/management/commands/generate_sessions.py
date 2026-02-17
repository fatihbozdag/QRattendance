from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.attendance.models import ClassSession, Course, Schedule


class Command(BaseCommand):
    help = "Pre-generate ClassSessions for the semester based on schedules"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            required=True,
            help="Semester start date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            help="Number of weeks (defaults to course.total_weeks)",
        )
        parser.add_argument(
            "--course",
            help="Generate for a specific course code only",
        )

    def handle(self, *args, **options):
        start_date = date.fromisoformat(options["start_date"])

        courses = Course.objects.all()
        if options["course"]:
            courses = courses.filter(code=options["course"])

        total_created = 0
        for course in courses:
            weeks = options["weeks"] or course.total_weeks
            schedules = Schedule.objects.filter(course=course)

            for schedule in schedules:
                for week in range(weeks):
                    # Calculate the date for this day_of_week in this week
                    days_ahead = schedule.day_of_week - start_date.weekday()
                    if days_ahead < 0:
                        days_ahead += 7
                    session_date = start_date + timedelta(days=days_ahead + (week * 7))

                    _, created = ClassSession.objects.get_or_create(
                        course=course,
                        date=session_date,
                        start_time=schedule.start_time,
                        defaults={
                            "end_time": schedule.end_time,
                            "week_number": week + 1,
                        },
                    )
                    if created:
                        total_created += 1

            self.stdout.write(f"  {course.code}: processed {weeks} weeks")

        self.stdout.write(self.style.SUCCESS(f"\nCreated {total_created} sessions total."))

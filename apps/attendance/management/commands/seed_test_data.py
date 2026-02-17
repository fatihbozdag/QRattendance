from datetime import time

from django.core.management.base import BaseCommand

from apps.attendance.models import Course, Schedule


class Command(BaseCommand):
    help = "Seed 4 test courses with schedules"

    def handle(self, *args, **options):
        courses_data = [
            {
                "code": "ELT101",
                "name": "Introduction to Linguistics",
                "semester": "2025-Spring",
                "schedules": [
                    {"day": 0, "start": time(9, 0), "end": time(10, 50)},   # Monday
                    {"day": 2, "start": time(9, 0), "end": time(10, 50)},   # Wednesday
                ],
            },
            {
                "code": "ELT201",
                "name": "Second Language Acquisition",
                "semester": "2025-Spring",
                "schedules": [
                    {"day": 1, "start": time(11, 0), "end": time(12, 50)},  # Tuesday
                    {"day": 3, "start": time(11, 0), "end": time(12, 50)},  # Thursday
                ],
            },
            {
                "code": "ELT301",
                "name": "Corpus Linguistics",
                "semester": "2025-Spring",
                "schedules": [
                    {"day": 0, "start": time(13, 0), "end": time(14, 50)},  # Monday
                    {"day": 3, "start": time(13, 0), "end": time(14, 50)},  # Thursday
                ],
            },
            {
                "code": "ELT401",
                "name": "Research Methods in Applied Linguistics",
                "semester": "2025-Spring",
                "schedules": [
                    {"day": 2, "start": time(15, 0), "end": time(16, 50)},  # Wednesday
                    {"day": 4, "start": time(15, 0), "end": time(16, 50)},  # Friday
                ],
            },
        ]

        for data in courses_data:
            course, created = Course.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "semester": data["semester"],
                },
            )
            status = "Created" if created else "Exists"

            for sched in data["schedules"]:
                Schedule.objects.get_or_create(
                    course=course,
                    day_of_week=sched["day"],
                    start_time=sched["start"],
                    defaults={"end_time": sched["end"]},
                )

            self.stdout.write(self.style.SUCCESS(f"  {status}: {course.code} — {course.name}"))

        self.stdout.write(self.style.SUCCESS("\nTest data seeded."))

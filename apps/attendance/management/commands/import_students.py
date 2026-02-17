from django.core.management.base import BaseCommand, CommandError

from apps.attendance.importers import (
    detect_course_code,
    import_students_to_course,
    parse_ubys_student_list,
)
from apps.attendance.models import Course


class Command(BaseCommand):
    help = "Import students from a UBYS attendance list (.xls) and enroll them in a course"

    def add_arguments(self, parser):
        parser.add_argument("file", help="Path to the .xls file")
        parser.add_argument(
            "--course",
            help="Course code to enroll students in (auto-detected from file if not given)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without saving",
        )

    def handle(self, *args, **options):
        filepath = options["file"]

        try:
            students = parse_ubys_student_list(filepath)
        except Exception as e:
            raise CommandError(f"Cannot read file: {e}")

        course_code = options.get("course")
        if not course_code:
            try:
                course_code = detect_course_code(filepath)
            except Exception:
                pass

        if not course_code:
            raise CommandError("Could not detect course code. Use --course to specify it.")

        try:
            course = Course.objects.get(code=course_code)
        except Course.DoesNotExist:
            raise CommandError(f"Course '{course_code}' not found. Create it first in admin.")

        self.stdout.write(f"Course: {course.code} — {course.name}")
        self.stdout.write(f"Found {len(students)} students")

        if options["dry_run"]:
            for sid, name in students:
                self.stdout.write(f"  {sid} — {name}")
            self.stdout.write(self.style.WARNING("Dry run — nothing saved."))
            return

        created_students, created_enrollments = import_students_to_course(course, students)

        self.stdout.write(self.style.SUCCESS(
            f"Done: {created_students} new students, {created_enrollments} new enrollments"
        ))

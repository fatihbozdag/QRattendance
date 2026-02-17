import os

import qrcode
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.attendance.models import Course


class Command(BaseCommand):
    help = "Generate QR code images for all courses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default="http://localhost:8000",
            help="Base URL of the deployed site (e.g. https://yourapp.railway.app)",
        )
        parser.add_argument(
            "--course",
            help="Generate for a specific course code only",
        )

    def handle(self, *args, **options):
        base_url = options["base_url"].rstrip("/")
        output_dir = os.path.join(settings.MEDIA_ROOT, "qr_codes")
        os.makedirs(output_dir, exist_ok=True)

        courses = Course.objects.all()
        if options["course"]:
            courses = courses.filter(code=options["course"])

        for course in courses:
            url = f"{base_url}/a/{course.qr_token}/"
            img = qrcode.make(url, box_size=10, border=2)
            filename = f"{course.code}_{course.semester}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            self.stdout.write(self.style.SUCCESS(f"Generated: {filename} → {url}"))

        self.stdout.write(self.style.SUCCESS(f"\nQR codes saved to: {output_dir}"))

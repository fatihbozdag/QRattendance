import uuid

from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Holiday(TimeStampedModel):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} — {self.name}"


class Student(TimeStampedModel):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self):
        return f"{self.student_id} — {self.name}"


class Course(TimeStampedModel):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    semester = models.CharField(max_length=20, help_text="e.g. 2025-Spring")
    lecturer = models.CharField(max_length=200, blank=True, help_text="e.g. Dr. Fatih Bozdag")
    course_hours = models.PositiveIntegerField(
        default=3, help_text="Weekly hours (e.g. 2, 3, 4)"
    )
    semester_start_date = models.DateField(
        null=True, blank=True,
        help_text="First day of semester — used to auto-generate 14 weeks of sessions",
    )
    total_weeks = models.PositiveIntegerField(default=14)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.semester}")
        super().save(*args, **kwargs)


class Enrollment(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    midterm_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ["student", "course"]
        ordering = ["course", "student"]
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        return f"{self.student.student_id} → {self.course.code}"


class Schedule(TimeStampedModel):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_before_minutes = models.PositiveIntegerField(default=5)
    grace_after_minutes = models.PositiveIntegerField(default=15)

    class Meta:
        ordering = ["course", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.course.code} — {self.get_day_of_week_display()} {self.start_time}–{self.end_time}"


class ClassSession(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    week_number = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        unique_together = ["course", "date", "start_time"]
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["course", "is_cancelled"]),
            models.Index(fields=["course", "date"]),
        ]

    def __str__(self):
        return f"{self.course.code} — {self.date} W{self.week_number}"

    @property
    def attendance_count(self):
        return self.records.count()


class AttendanceRecord(TimeStampedModel):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(
        Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_records"
    )
    student_id_entered = models.CharField(max_length=20, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["session", "student_id_entered"]
        indexes = [
            models.Index(fields=["session", "ip_address"]),
            models.Index(fields=["student"]),
        ]

    def __str__(self):
        return f"{self.student_id_entered} @ {self.session}"


class ExcusedAbsence(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="excused_absences")
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="excused_absences")
    reason = models.CharField(max_length=200, help_text='e.g. "Medical report", "Official leave"')

    class Meta:
        unique_together = ["student", "session"]
        ordering = ["session__date"]
        indexes = [
            models.Index(fields=["student", "session"]),
        ]

    def __str__(self):
        return f"{self.student.student_id} — {self.session} (Excused)"


class CourseMaterial(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="materials/", blank=True)
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.file and not self.url:
            raise ValidationError("At least one of 'file' or 'url' must be provided.")

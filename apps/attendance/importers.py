"""Shared import utilities for UBYS student list files."""

import pandas as pd

from .models import Enrollment, Student


def parse_ubys_student_list(file_obj):
    """Parse a UBYS .xls attendance list and return student data.

    Args:
        file_obj: A file path (str) or file-like object readable by pandas.

    Returns:
        list[tuple[str, str]]: List of (student_id, name) tuples.
    """
    df = pd.read_excel(file_obj)

    students = []
    for _, row in df.iterrows():
        student_id = row.iloc[4]
        name = row.iloc[5]

        if pd.isna(student_id) or pd.isna(name):
            continue

        student_id = (
            str(int(student_id)) if isinstance(student_id, float) else str(student_id).strip()
        )
        name = str(name).strip()

        # Skip header rows
        if student_id in ("Öğrenci No", "#") or not student_id.isdigit():
            continue

        students.append((student_id, name))

    return students


def detect_course_code(file_obj):
    """Try to detect a course code from the UBYS header area.

    Args:
        file_obj: A file path (str) or file-like object readable by pandas.

    Returns:
        str or None: The detected course code, or None.
    """
    df = pd.read_excel(file_obj)

    for i in range(min(5, len(df))):
        for j in range(len(df.columns)):
            val = df.iloc[i, j]
            if pd.isna(val):
                continue
            val = str(val)
            # UBYS format: "IMT412\n1" (code + section)
            if "\n" in val:
                code = val.split("\n")[0].strip()
                if len(code) >= 4 and any(c.isdigit() for c in code):
                    return code
    return None


def import_students_to_course(course, students):
    """Create Student records and Enrollment links for a course.

    Args:
        course: A Course instance.
        students: list[tuple[str, str]] — (student_id, name) pairs.

    Returns:
        tuple[int, int]: (created_students, created_enrollments)
    """
    created_students = 0
    created_enrollments = 0

    for student_id, name in students:
        student, created = Student.objects.get_or_create(
            student_id=student_id,
            defaults={"name": name},
        )
        if created:
            created_students += 1

        _, enrolled = Enrollment.objects.get_or_create(
            student=student,
            course=course,
        )
        if enrolled:
            created_enrollments += 1

    return created_students, created_enrollments

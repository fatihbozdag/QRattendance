from django.urls import path

from . import instructor_views

app_name = "instructor"

urlpatterns = [
    path("", instructor_views.instructor_course_list, name="course_list"),
    path("course/<int:course_id>/", instructor_views.instructor_course_dashboard, name="course_dashboard"),
    path("course/<int:course_id>/attendance/", instructor_views.instructor_attendance_matrix, name="attendance_matrix"),
    path("course/<int:course_id>/qr/", instructor_views.instructor_qr_code, name="qr_code"),
    path("course/<int:course_id>/grades/", instructor_views.instructor_import_grades, name="import_grades"),
    path("course/<int:course_id>/materials/", instructor_views.instructor_materials, name="materials"),
]

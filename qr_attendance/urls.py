from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from apps.attendance.admin_views import attendance_matrix, course_qr_code

urlpatterns = [
    path("admin/attendance/matrix/<int:course_id>/", attendance_matrix, name="attendance_matrix"),
    path("admin/attendance/qr/<int:course_id>/", course_qr_code, name="course_qr_code"),
    path("admin/", admin.site.urls),
    path("a/", include("apps.attendance.urls")),
    path("api/", include("apps.api.urls")),
    path("portal/", include("apps.portal.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

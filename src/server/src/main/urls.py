from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("auth/", include("users.urls")),
    path("admin/", admin.site.urls, name="admin"),
    path("app/", include("app.urls"), name="app"),
]

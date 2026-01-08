from django.urls import path, include
from .api import api


urlpatterns = [
    path("file-form/", include("django_file_form.urls")),
    path("api/", api.urls),
]

from django.urls import path
from voting.views import (
    index,
)


urlpatterns = [
    path("", index, name="index"),
]

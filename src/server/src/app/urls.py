from django.urls import path, include
from .api import api
from .views import voting_playground_view, voting_view


urlpatterns = [
    path("file-form/", include("django_file_form.urls")),
    path("api/", api.urls),
    path("vote/", voting_view, name="vote"),
    path("vote/playground/", voting_playground_view, name="vote_playground"),
]

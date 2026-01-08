from django.urls import path
from django.views.generic import RedirectView
from allauth.account import views as account_views


urlpatterns = [
    path(
        "login/",
        account_views.request_login_code,
        name="account_request_login_code",
    ),
    path(
        "verify/",
        account_views.confirm_login_code,
        name="account_confirm_login_code",
    ),
    path(
        "logout/",
        account_views.logout,
        name="account_logout",
    ),
    path(
        "signup/",
        RedirectView.as_view(pattern_name="account_request_login_code"),
        name="account_signup",
    ),
    path(
        "signin/",
        RedirectView.as_view(pattern_name="account_request_login_code"),
        name="account_login",
    ),
]

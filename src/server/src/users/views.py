import uuid
from django.contrib.auth import login, get_user_model
from django.shortcuts import redirect, render
from random_username.generate import generate_username
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from users.models import Voter, NaturalVector
from users.adapters import UnifiedRequestLoginCodeForm
from allauth.account.adapter import get_adapter

User = get_user_model()


@require_POST
def guest_login_view(request):
    """Creates a guest user and logs them in."""
    username = generate_username(1)[0]
    user = User.objects.create_user(
        username=f"{username}",
        email=f"{username}@anon.cosound.io",
        password=None,
    )

    if not hasattr(user, "voter"):
        nvec = NaturalVector.null()
        nvec.save()
        Voter.objects.create(user=user, nvec=nvec)

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    if request.headers.get("HX-Request"):
        return HttpResponse(status=204, headers={"HX-Trigger": "authSuccess"})

    return redirect(request.GET.get("next", "/"))


def htmx_auth_options(request):
    """Render the initial modal options."""
    return render(request, "account/partials/auth_options.html")


def htmx_login_email(request):
    """
    Step 1: Validate email (auto-signup if new), generate code, and send it.
    """
    form = UnifiedRequestLoginCodeForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        adapter = get_adapter(request)

        # Generate & Send Code
        code = adapter.generate_login_code()
        adapter.send_mail("account/email/login_code", email, {"code": code})

        # Store simple state in session (don't use set_expiry - it affects entire session!)
        request.session["login_code"] = code
        request.session["login_email"] = email

        return render(request, "account/partials/login_code.html", {"email": email})

    return render(request, "account/partials/login_email.html", {"form": form})


def htmx_login_code(request):
    """
    Step 2: Verify code and login.
    """
    email = request.session.get("login_email")
    correct_code = request.session.get("login_code")

    if not email or not correct_code:
        # Session expired or invalid flow -> Reset to start
        return render(request, "account/partials/auth_options.html")

    error = None
    if request.method == "POST":
        input_code = request.POST.get("code", "").strip()

        if input_code == correct_code:
            try:
                user = User.objects.get(email__iexact=email)
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )

                # Cleanup
                del request.session["login_code"]
                del request.session["login_email"]

                return HttpResponse(status=204, headers={"HX-Trigger": "authSuccess"})
            except User.DoesNotExist:
                error = "User not found."
        else:
            error = "Invalid code."

    return render(
        request,
        "account/partials/login_code.html",
        {"email": email, "error": error, "value": request.POST.get("code", "")},
    )

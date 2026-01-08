import uuid
import random
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import RequestLoginCodeForm
from django.contrib.auth import get_user_model
from django import forms
from users.models import Voter, NaturalVector


class UnifiedLoginAdapter(DefaultAccountAdapter):
    def generate_login_code(self):
        return "".join(random.choices("0123456789", k=6))

    def is_open_for_signup(self, request):
        return True


class UnifiedRequestLoginCodeForm(RequestLoginCodeForm):
    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()

        User = get_user_model()
        if not User.objects.filter(email__iexact=email).exists():
            base_username = email.split("@")[0]
            unique_suffix = uuid.uuid4().hex[:8]
            username = f"{base_username}_{unique_suffix}"

            user = User.objects.create(
                email=email,
                username=username,
            )
            user.set_unusable_password()
            user.save()
        else:
            user = User.objects.get(email__iexact=email)

        if not Voter.objects.filter(user=user).exists():
            nvector = NaturalVector.null()
            nvector.save()
            voter = Voter.objects.create(
                user=user,
                nvector=nvector,
            )
            voter.save()
        return super().clean_email()

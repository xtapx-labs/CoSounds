from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.files.base import File
import secrets
import random


class User(AbstractUser):
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class Client(models.Model):
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name="Client Name")
    billing_address = models.TextField(
        verbose_name="Client Billing Address", blank=True
    )
    token = models.CharField(max_length=64, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)  # Secure random key
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class NaturalVector(models.Model):
    rain = models.FloatField()
    sea_waves = models.FloatField()
    thunderstorm = models.FloatField()
    wind = models.FloatField()
    crackling_fire = models.FloatField()

    @classmethod
    def null(cls) -> "NaturalVector":
        return cls(
            rain=0,
            sea_waves=0,
            thunderstorm=0,
            wind=0,
            crackling_fire=0,
        )

    @classmethod
    def classify(cls, audio_file: File) -> "NaturalVector":
        return cls(
            rain=random.uniform(0, 1),
            sea_waves=random.uniform(0, 1),
            thunderstorm=random.uniform(0, 1),
            wind=random.uniform(0, 1),
            crackling_fire=random.uniform(0, 1),
        )


class Voter(models.Model):
    class Meta:
        verbose_name = "Voter"
        verbose_name_plural = "Voters"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nvector = models.ForeignKey(NaturalVector, on_delete=models.PROTECT)

    def __str__(self):
        return f"Voter: {self.user.username}"

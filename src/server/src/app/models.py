import random
import secrets
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from users.models import NaturalVector

from app.ml import classify_sound


class Player(models.Model):
    client = models.ForeignKey(
        "users.Client",
        on_delete=models.CASCADE,
        verbose_name="Client Owner",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Name of Player",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
    )
    library = models.ManyToManyField(
        "Sound",
        verbose_name="Library",
        blank=True,
    )
    cosound = models.JSONField(
        verbose_name="Cosound",
        default=dict,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def summary(self):
        string = ""
        soundscapes = self.cosound.get("soundscapes", [])

        for i, soundscape in enumerate(soundscapes):
            sound = Sound.objects.get(id=soundscape["id"])
            string += f"\t  Soundscape Layer {i+1}: {sound.title}\n"
            gains = soundscape["gain"]
            for group, gain in gains.items():  # type: ignore
                string += f"\t\t-> {group.capitalize()} Gain: {gain:.2f}\n"

        instrumentals = self.cosound.get("instrumental", [])
        if len(instrumentals) > 0:
            for i, instrumental in enumerate(instrumentals):
                sound = Sound.objects.get(id=instrumental["id"])
                string += f"\t  Instrumental Layer {i+1}: {sound.title}\n"
                gains = instrumental["gain"]
                for group, gain in gains.items():  # type: ignore
                    string += f"\t\t-> {group.capitalize()} Gain: {gain:.2f}\n"
        return string

    def toJson(self) -> dict:
        """Serialize Player instance."""
        return {
            "id": self.id,
            "name": self.name,
            "client_id": self.client_id,
        }

    def __str__(self):
        return self.name


class Sound(models.Model):
    audio = models.FileField(
        upload_to="sounds/audio/",
        verbose_name="Audio File",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Sound Title",
    )
    artist = models.CharField(
        verbose_name="Recording Artist",
        max_length=255,
    )
    nvec = models.ForeignKey(
        NaturalVector,
        on_delete=models.CASCADE,
        verbose_name="Natural Vector of Sound",
        null=True,
        blank=True,
    )
    type = models.CharField(
        max_length=50,
        verbose_name="Type of Sound",
        choices=[
            ("Instrumental", "Instrumental"),
            ("Soundscape", "Soundscape"),
            ("Vocal", "Vocal Music"),
        ],
    )
    timestamp = models.DateTimeField(
        auto_now=True,
        verbose_name="Time Stamp",
    )

    def save(self, *args, **kwargs):
        if not self.nvec:
            embeddings = classify_sound(self.audio)
            nvec = NaturalVector.fromList(embeddings)
            nvec.save()
            self.nvec = nvec
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title + " by " + self.artist

    def get_inline_title(self):
        return f"{self.title}"

    def toJson(self) -> dict:
        """Serialize Sound instance with full URL for audio file."""
        return {
            "id": self.id,
            "audio": self.audio.url,  # Full S3 URL
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "artist": self.artist,
            "nvec": self.nvec.toList(),
            "type": self.type,
        }


class Vote(models.Model):
    upvote = models.BooleanField(
        verbose_name="Upvote",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp",
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Voter",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        verbose_name="Player",
    )
    group = models.CharField(
        max_length=255,
        verbose_name="Group",
        null=True,
        blank=True,
    )
    cosound = models.JSONField(
        verbose_name="Cosound",
        default=dict,
        blank=True,
        null=True,
    )

    def __str__(self):
        vote_type = "Upvote" if self.upvote else "Downvote"
        return f"{vote_type} by {self.voter.username} at {self.player.name}"

    def toJson(self) -> dict:
        """Serialize Vote instance."""
        return {
            "id": self.id,
            "upvote": self.upvote,
            "timestamp": self.timestamp.isoformat(),
            "voter": self.voter_id,
            "group": self.group,
        }

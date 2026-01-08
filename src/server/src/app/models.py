import random
import secrets
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from users.models import NaturalVector


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

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)
        super().save(*args, **kwargs)

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
    # The Type of Sound only choices: Instrumental, Soundscape, Vocal
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
            nvec = NaturalVector.classify(self.audio)
            nvec.save()
            self.nvec = nvec
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_inline_title(self):
        return f"{self.title}"


class Cosound(models.Model):
    sounds = models.ManyToManyField(
        Sound,
        verbose_name="Sounds",
    )
    gain = models.JSONField(
        verbose_name="Gain for each Sound",
        default=dict,
        blank=True,
        null=True,
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        verbose_name="Player",
    )

    def save(self, *args, **kwargs):

        if self.pk is None:  # Must save before we can access self.sounds
            super().save(*args, **kwargs)
            return
        player = self.player
        if self.sounds.count() > 0:
            for sound in self.sounds.all():
                if sound not in player.library.all():
                    raise ValidationError(
                        f"Cosound can only be composed of Sounds in the Player's library."
                    )

            self.gain = {} if not self.gain else self.gain
            for sound in self.sounds.all():
                # Ensure keys are strings for JSONField
                s_id = str(sound.id)
                if s_id not in self.gain:
                    self.gain[s_id] = {"global": 1.0}
                if "global" not in self.gain[s_id].keys():
                    self.gain[s_id]["global"] = 1.0

        super().save(*args, **kwargs)

    def summary(self):

        string = ""
        for i, sound in enumerate(self.sounds.all()):
            string += f"\t  Layer {i+1}: {sound.title}\n"
            for group, gain in self.gain[str(sound.id)].items():  # type: ignore
                string += f"\t\t-> {group.capitalize()} Gain: {gain:.2f}\n"
        return string

    def __str__(self):
        if not self.pk:
            return "Unsaved Cosound"
        count = self.sounds.count()
        if count == 0:
            return "Empty Cosound"
        elif count == 1:
            return f"Single Layer Cosound : {self.sounds.first().title}"  # type: ignore
        else:
            return f"Multi-Layer Cosound ({count} Sounds)"


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
    cosound = models.ForeignKey(
        Cosound,
        on_delete=models.CASCADE,
        verbose_name="Cosound",
    )

    def __str__(self):
        vote_type = "Upvote" if self.upvote else "Downvote"
        return f"{vote_type} by {self.voter.username} on {self.cosound}"

import datetime
import random
import time

from django.utils import timezone


def predict_cosound(
    player: dict,
    votes: list[dict],
    voters: list[dict],
    soundscapes: list[dict],
    instrumentals: list[dict],
) -> dict:
    time.sleep(5)  # Simulate Heavy Work

    predicted_soundscapes: list[dict] = []
    for soundscape in random.sample(soundscapes, min(3, len(soundscapes))):
        predicted_soundscapes.append(
            {
                "id": soundscape["id"],
                "gain": {"global": 1.0},
                "timestamp": soundscape["timestamp"],
                "path": soundscape["audio"],
            }
        )

    predicted_instrumental: list[dict] = []
    if instrumentals and random.choice([True, False]):
        for instrumental in random.sample(instrumentals, min(1, len(instrumentals))):
            predicted_instrumental.append(
                {
                    "id": instrumental["id"],
                    "gain": {"global": 0.3},
                    "timestamp": instrumental["timestamp"],
                    "path": instrumental["audio"],
                }
            )

    return {
        "soundscapes": predicted_soundscapes,
        "instrumental": predicted_instrumental,
        "timestamp": timezone.now().isoformat(),
    }


def classify_sound(file):
    return [
        random.uniform(0, 1),  # Rain Sounds
        random.uniform(0, 1),  # Sea Waves
        random.uniform(0, 1),  # Thunderstorm
        random.uniform(0, 1),  # Wind
        random.uniform(0, 1),  # Crackling Fire
    ]


def classify_voter(data):
    return [
        random.uniform(0, 1),  # Rain Sounds
        random.uniform(0, 1),  # Sea Waves
        random.uniform(0, 1),  # Thunderstorm
        random.uniform(0, 1),  # Wind
        random.uniform(0, 1),  # Crackling Fire
    ]

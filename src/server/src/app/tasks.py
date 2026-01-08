import datetime
import random
import time
from typing import Optional
from django.tasks import task
from app.models import Cosound, Sound, Player, Vote


@task
def refresh_player(player_id: int) -> int:
    # Remove the try/except block so you can see errors in your logs!
    player = Player.objects.get(id=player_id)

    cosound = predict_cosound(
        player=player,
        available_sounds=list(player.library.all()),
        votes=list(
            Vote.objects.filter(
                player=player,
                timestamp__date=datetime.date.today(),
            )
        ),
    )
    return cosound.id  # type: ignore


def predict_cosound(
    player: Player,
    available_sounds: list[Sound],
    votes: Optional[list[Vote]] = None,
) -> Cosound:
    assert len(available_sounds) > 0, "No sounds available"

    # 1. Simulate heavy work
    time.sleep(3)

    # 2. Pick sounds
    sounds = random.sample(
        available_sounds,
        k=min(3, len(available_sounds)),
    )

    # 3. FIX: Create Cosound first (without sounds)
    cosound = Cosound.objects.create(player=player)

    # 4. FIX: Set the Many-to-Many relationship afterwards
    cosound.sounds.set(sounds)

    # Example Regions for Player Groups. Dummy at the moment.
    # Needs to be configured at the Player Level to work.
    player_groups = ["Global", "Rear Door", "Front Door"]
    gains = {}

    for sound in sounds:
        # Example random gain calculation
        for group in player_groups:
            gains.setdefault(str(sound.id), {})[group] = random.uniform(0.5, 1.0)

    # 5. Save again (triggers your custom save logic/gain calculation)
    cosound.save()

    return cosound

import datetime
import random
import time

from django.contrib.auth import get_user_model
from django.tasks import task
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from app.models import Player, Vote
from app.ml import predict_cosound
from users.models import Voter


@task
def refresh_player(player_id: int) -> str:
    player = Player.objects.get(id=player_id)

    # Serialize player
    player_data = player.toJson()

    # Get timestamp of last cosound refresh
    default_last_refresh = timezone.make_aware(datetime.datetime(1970, 1, 1))
    last_refresh_str = player.cosound.get("timestamp") if player.cosound else None

    # Parse the ISO timestamp string to a datetime object
    if last_refresh_str:
        last_refresh = parse_datetime(last_refresh_str)
        if last_refresh is None:
            last_refresh = default_last_refresh
    else:
        last_refresh = default_last_refresh

    # Serialize all votes of this player that occured after last refresh
    votes_data = [
        vote.toJson()
        for vote in Vote.objects.filter(player=player, timestamp__gt=last_refresh)
    ]

    if not votes_data:
        refresh_anyway = random.random() < 0.9  # 33% chance to refresh anyway
        if not refresh_anyway:
            return ""

    # Extract unique voters ids from votes
    seen_voter_ids = set()
    for vote in votes_data:
        voter_id = vote["voter"]
        if voter_id not in seen_voter_ids:
            seen_voter_ids.add(voter_id)

    # Serialize Voters from Voter IDs
    voters_data = []
    for voter_id in seen_voter_ids:
        try:
            voter = Voter.objects.get(user_id=voter_id)
            voters_data.append(voter.toJson())
        except Voter.DoesNotExist:
            # Skip voters that don't exist (e.g., deleted users)
            continue

    # Serialize sounds from player's library
    soundscapes_data = [
        sound.toJson() for sound in player.library.filter(type="Soundscape")
    ]

    # Serialize instrumentals from player's library
    instrumentals_data = [
        sound.toJson() for sound in player.library.filter(type="Instrumental")
    ]

    # Get our prediction
    prediction = predict_cosound(
        player=player_data,
        votes=votes_data,
        voters=voters_data,
        soundscapes=soundscapes_data,
        instrumentals=instrumentals_data,
    )

    player.cosound = prediction
    player.save(update_fields=["cosound"])
    return player.summary()

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Player, Vote, Sound


def voting_playground_view(request):
    return render(request, "voter/playground/index.html")


def extract_sound_ids(cosound):
    sound_ids = []
    if cosound:
        for sound_list in cosound.values():
            if isinstance(sound_list, list):
                for sound_data in sound_list:
                    if isinstance(sound_data, dict) and "id" in sound_data:
                        sound_ids.append(sound_data["id"])
    return sound_ids


def voting_view(request):
    # Get URL parameters
    player_token = request.GET.get("player_token")
    choice = request.GET.get("choice")

    # Validate parameters
    if not player_token or choice is None:
        return HttpResponse(
            "Missing required parameters: player_token and choice", status=400
        )

    # Convert choice to boolean
    upvote = choice.lower() in ["true", "1", "yes"]

    # Get the player object
    player = get_object_or_404(Player, token=player_token)

    # Check if user is logged in
    if not request.user.is_authenticated:
        return render(
            request,
            "voter/voting/index.html",
            {
                "requires_login": True,
                "player": player,
            },
        )

    # Get voter card data
    voter_vote_count = Vote.objects.filter(voter=request.user).count()
    voter_data = {
        "num_votes": voter_vote_count,
        "join_date": request.user.date_joined.strftime("%b %Y"),
        "username": request.user.username,
        "user_id": request.user.id,
    }

    # User is logged in, check rate limiting (60 seconds)
    one_minute_ago = timezone.now() - timedelta(seconds=60)
    recent_vote = Vote.objects.filter(
        voter=request.user, player=player, timestamp__gte=one_minute_ago
    ).first()

    if recent_vote:
        # Build layers for rate-limited view
        cosound = player.cosound
        layers = []
        if cosound:
            sound_ids = extract_sound_ids(cosound)
            sounds = Sound.objects.filter(id__in=sound_ids) if sound_ids else []
            sounds_dict = {sound.id: sound for sound in sounds}
            layer_index = 1

            for sound_data in cosound.get("soundscapes", []):
                sound_id = sound_data.get("id")
                if sound_id and sound_id in sounds_dict:
                    sound = sounds_dict[sound_id]
                    gains = sound_data.get("gain", {})
                    gain_value = next(iter(gains.values()), 0.5) if gains else 0.5
                    layers.append(
                        {
                            "id": f"item{layer_index}",
                            "layer_type": "Soundscape Layer",
                            "gain_level": f"{gain_value:.2f}",
                            "sound_name": sound.title,
                            "recording_artist": sound.artist,
                            "artwork_url": f"https://picsum.photos/seed/{sound_id}/400/400",
                        }
                    )
                    layer_index += 1

            for sound_data in cosound.get("instrumental", []):
                sound_id = sound_data.get("id")
                if sound_id and sound_id in sounds_dict:
                    sound = sounds_dict[sound_id]
                    gains = sound_data.get("gain", {})
                    gain_value = next(iter(gains.values()), 0.5) if gains else 0.5
                    layers.append(
                        {
                            "id": f"item{layer_index}",
                            "layer_type": "Instrumental Layer",
                            "gain_level": f"{gain_value:.2f}",
                            "sound_name": sound.title,
                            "recording_artist": sound.artist,
                            "artwork_url": f"https://picsum.photos/seed/{sound_id}/400/400",
                        }
                    )
                    layer_index += 1

        return render(
            request,
            "voter/voting/index.html",
            {
                "rate_limited": True,
                "player": player,
                "client": player.client,
                "recent_vote": recent_vote,
                "last_vote_timestamp": recent_vote.timestamp,
                "layers": layers,
                "voter_data": voter_data,
            },
        )

    # Get the cosound from the player's JSON field
    cosound = player.cosound

    if not cosound:
        return HttpResponse("No cosound available for this player", status=404)

    # Create the vote
    voter_obj = request.user if not request.user.is_anonymous else None

    vote = Vote.objects.create(
        upvote=upvote,
        voter=request.user,
        player=player,
        cosound=cosound,
    )

    # Get Sound objects from cosound JSON and build layer data
    sound_ids = extract_sound_ids(cosound)
    sounds = Sound.objects.filter(id__in=sound_ids) if sound_ids else []
    sounds_dict = {sound.id: sound for sound in sounds}

    # Build enriched layer data for cotton components
    layers = []
    layer_index = 1

    # Process soundscapes
    for sound_data in cosound.get("soundscapes", []):
        sound_id = sound_data.get("id")
        if sound_id and sound_id in sounds_dict:
            sound = sounds_dict[sound_id]
            gains = sound_data.get("gain", {})
            # Use the first gain value or default to 0.5
            gain_value = next(iter(gains.values()), 0.5) if gains else 0.5
            layers.append(
                {
                    "id": f"item{layer_index}",
                    "layer_type": "Soundscape Layer",
                    "gain_level": f"{gain_value:.2f}",
                    "sound_name": sound.title,
                    "recording_artist": sound.artist,
                    "artwork_url": f"https://picsum.photos/seed/{sound_id}/400/400",
                }
            )
            layer_index += 1

    # Process instrumentals
    for sound_data in cosound.get("instrumental", []):
        sound_id = sound_data.get("id")
        if sound_id and sound_id in sounds_dict:
            sound = sounds_dict[sound_id]
            gains = sound_data.get("gain", {})
            gain_value = next(iter(gains.values()), 0.5) if gains else 0.5
            layers.append(
                {
                    "id": f"item{layer_index}",
                    "layer_type": "Instrumental Layer",
                    "gain_level": f"{gain_value:.2f}",
                    "sound_name": sound.title,
                    "recording_artist": sound.artist,
                    "artwork_url": f"https://picsum.photos/seed/{sound_id}/400/400",
                }
            )
            layer_index += 1

    # Render the voting view with all context
    return render(
        request,
        "voter/voting/index.html",
        {
            "vote": vote,
            "player": player,
            "client": player.client,
            "voter": voter_obj,
            "sounds": sounds,
            "layers": layers,
            "success": True,
            "voter_data": voter_data,
        },
    )

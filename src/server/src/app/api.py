from typing import List

from django.contrib.auth import authenticate
from ninja import NinjaAPI
from ninja.orm import ModelSchema
from ninja.security import APIKeyHeader, HttpBasicAuth
from ninja.throttling import AuthRateThrottle

from app.models import Player, Sound
from users.models import Client

api = NinjaAPI()


class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        return authenticate(
            request,
            username=username,
            password=password,
        )


class ClientOut(ModelSchema):
    class Meta:
        model = Client
        fields = ["name", "token"]


@api.get(
    "/client/list",
    response=List[ClientOut],
    auth=BasicAuth(),
    throttle=[AuthRateThrottle("10/m")],
)
def get_clients(request):
    return Client.objects.filter(user=request.auth)


class PersonalTokenAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        try:
            return Client.objects.get(token=key)
        except Client.DoesNotExist:
            return None


class PlayerOut(ModelSchema):
    class Meta:
        model = Player
        fields = ["name", "token"]


@api.get(
    "/player/list",
    response=List[PlayerOut],
    auth=PersonalTokenAuth(),
    throttle=[AuthRateThrottle("10/m")],
)
def get_players(request):
    client: Client = request.auth
    return Player.objects.filter(client=client)


class SoundOut(ModelSchema):
    class Meta:
        model = Sound
        fields = ["id", "type", "audio", "timestamp"]


@api.get(
    "/player/library",
    response=List[SoundOut],
    auth=PersonalTokenAuth(),
    throttle=[AuthRateThrottle("10/m")],
)
def get_player_library(request, player: str):
    client: Client = request.auth
    try:
        player_obj = Player.objects.get(token=player, client=client)
    except Player.DoesNotExist:
        return api.create_response(
            request,
            {"detail": "Player not found."},
            status=404,
        )

    return player_obj.library.all()


@api.get(
    "/cosound",
    auth=PersonalTokenAuth(),
    throttle=[AuthRateThrottle("10/m")],
)
def get_cosound(request, player: str):
    client: Client = request.auth
    try:
        player_obj = Player.objects.get(token=player, client=client)
        cosound_data = player_obj.cosound or {}

        # Get full Sound objects for soundscapes
        soundscapes_with_sounds = []
        for soundscape in cosound_data.get("soundscapes", []):
            try:
                sound = Sound.objects.get(id=soundscape["id"])
                soundscapes_with_sounds.append(
                    {
                        "id": sound.id,
                        "audio": sound.audio.url,
                        "title": sound.title,
                        "artist": sound.artist,
                        "type": sound.type,
                        "timestamp": sound.timestamp.isoformat(),
                        "gain": soundscape.get("gain", {"global": 1.0}),
                    }
                )
            except Sound.DoesNotExist:
                continue

        # Get full Sound objects for instrumentals
        instrumentals_with_sounds = []
        for instrumental in cosound_data.get("instrumental", []):
            try:
                sound = Sound.objects.get(id=instrumental["id"])
                instrumentals_with_sounds.append(
                    {
                        "id": sound.id,
                        "audio": sound.audio.url,
                        "title": sound.title,
                        "artist": sound.artist,
                        "type": sound.type,
                        "timestamp": sound.timestamp.isoformat(),
                        "gain": instrumental.get("gain", {"global": 1.0}),
                    }
                )
            except Sound.DoesNotExist:
                continue

        return {
            "soundscapes": soundscapes_with_sounds,
            "instrumental": instrumentals_with_sounds,
            "timestamp": cosound_data.get("timestamp"),
        }
    except Player.DoesNotExist:
        # Throw a 404 if the player does not exist or does not belong to the client
        return api.create_response(
            request,
            {"detail": "Player not found."},
            status=404,
        )

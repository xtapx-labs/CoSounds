import time
import sys
from django.core.management.base import BaseCommand
from app.models import Player
from app.tasks import refresh_player


class Command(BaseCommand):
    help = "Runs a continuous loop that triggers the generate_cosound task every 5 minutes."

    def add_arguments(self, parser):

        parser.add_argument("args", nargs="*")

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Initializing Cosound Generation Scheduler...")
        )
        try:
            while True:
                players = Player.objects.all()
                if players:
                    for player in players:
                        try:
                            result = refresh_player.enqueue(player_id=player.id)  # type: ignore
                            if result.return_value is not None:
                                summary = result.return_value  # type: ignore
                                bold_name = f"\033[1m{player.name}\033[22m"
                                if summary == "":
                                    continue
                                else:
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"\033[1m[Refreshing Cosound..]\033[22m Now Playing at {bold_name}:\n{summary}"
                                        )
                                    )
                        except (ValueError, Exception) as e:
                            # Log the error but continue processing other players
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Failed to refresh player {player.name}: {str(e)}"
                                )
                            )
                            continue
                else:
                    self.stdout.write(self.style.WARNING("No Active Players Found."))
                time.sleep(60)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nScheduler stopped by user."))
            sys.exit(0)

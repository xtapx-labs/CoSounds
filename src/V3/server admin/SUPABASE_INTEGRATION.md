# Django → Supabase Integration Guide

## Overview
This Django app connects to the same Supabase PostgreSQL database as the Node.js server, using **unmanaged models** to avoid migration conflicts.

## Step 1: Environment Configuration

Create `.env` file in project root or `env/.env`:

```bash
# Supabase Database Connection
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?pgbouncer=true
# Or direct connection:
# DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.com:5432/postgres

# AWS S3 for Audio Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=soundguys-audio
AWS_S3_REGION_NAME=us-east-1

# Supabase Auth (for JWT validation)
SUPABASE_URL=https://PROJECT_REF.supabase.com
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Django Secret
SECRET_KEY=your-django-secret-key-here
```

## Step 2: Install Dependencies

```bash
uv add psycopg2-binary pgvector django-storages boto3
```

## Step 3: Database Connection

The `settings.py` is already configured to use `DATABASE_URL`. Verify:

```python
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or "sqlite:///db.sqlite3",
        conn_max_age=600,
        ssl_require=bool(DATABASE_URL),
    )
}
```

## Step 4: Create Unmanaged Models

Replace `src/core/models.py` with Supabase-aligned models:

```python
from django.db import models
from pgvector.django import VectorField

class Profile(models.Model):
    """Unmanaged model for Supabase profiles table"""
    id = models.UUIDField(primary_key=True)
    email = models.EmailField()
    name = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    preference_vector = VectorField(dimensions=5, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False  # Django won't create/alter this table
        db_table = 'profiles'

class Song(models.Model):
    """Unmanaged model for Supabase songs table"""
    id = models.UUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, null=True, blank=True)
    file_url = models.URLField(max_length=500)  # S3 URL
    type = models.CharField(
        max_length=20,
        choices=[('soundscape', 'Soundscape'), ('instrumental', 'Instrumental')]
    )
    embedding = VectorField(dimensions=5, null=True)
    duration = models.IntegerField(null=True)
    bpm = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'songs'

class Player(models.Model):
    """Unmanaged model for Supabase players table"""
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('playing', 'Playing'),
            ('idle', 'Idle')
        ],
        default='offline'
    )
    current_song = models.ForeignKey(
        Song,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_players'
    )
    last_poll = models.DateTimeField(null=True, blank=True)
    manager = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_players'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'players'

class PlayerLibrary(models.Model):
    """Unmanaged model for player_library junction table"""
    id = models.UUIDField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'player_library'
        unique_together = [['player', 'song']]

class PlayerQueue(models.Model):
    """Unmanaged model for player_queue table"""
    id = models.UUIDField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'player_queue'
        unique_together = [['player', 'position']]
        ordering = ['position']

class Vote(models.Model):
    """Unmanaged model for votes table"""
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    vote_value = models.IntegerField()
    vote_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'votes'

class Session(models.Model):
    """Unmanaged model for sessions table"""
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'sessions'
```

## Step 5: Configure S3 Storage

Add to `settings.py`:

```python
# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_DEFAULT_ACL = 'public-read'
AWS_LOCATION = 'sounds'

# Use S3 for media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
```

## Step 6: Django Admin Configuration

Update `src/core/admin.py`:

```python
from django.contrib import admin
from .models import Song, Player, PlayerLibrary, PlayerQueue

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'type', 'duration', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['title', 'artist']
    readonly_fields = ['id', 'file_url', 'embedding', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        # When a file is uploaded, it goes to S3
        # The file_url is automatically set by django-storages
        super().save_model(request, obj, form, change)
        # TODO: Trigger ML embedding generation

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'current_song', 'last_poll', 'manager']
    list_filter = ['status']
    search_fields = ['name', 'token']
    readonly_fields = ['token', 'last_poll']

@admin.register(PlayerLibrary)
class PlayerLibraryAdmin(admin.ModelAdmin):
    list_display = ['player', 'song', 'added_at']
    list_filter = ['player']
    autocomplete_fields = ['player', 'song']

@admin.register(PlayerQueue)
class PlayerQueueAdmin(admin.ModelAdmin):
    list_display = ['player', 'song', 'position', 'added_at']
    list_filter = ['player']
    ordering = ['player', 'position']
```

## Step 7: Test Connection

```bash
# Test database connection
uv run python src/main.py check

# Create Django admin superuser (this WILL create a Django User, separate from Supabase)
uv run python src/main.py createsuperuser

# Run server
uv run python src/main.py runserver
```

## Step 8: Player API (Django Ninja)

Update `src/core/api.py` to read from Supabase:

```python
from ninja import NinjaAPI, Header
from .models import Player, PlayerQueue, Song

api = NinjaAPI()

@api.get("/player/queue")
def get_player_queue(request, player_token: str = Header(alias="X-API-Key")):
    """Player polls this endpoint to get next songs"""
    try:
        player = Player.objects.get(token=player_token)
        player.last_poll = timezone.now()
        player.status = 'online'
        player.save()

        # Get queue
        queue = PlayerQueue.objects.filter(player=player).select_related('song')
        return {
            "success": True,
            "songs": [
                {
                    "id": str(q.song.id),
                    "title": q.song.title,
                    "file_url": q.song.file_url,
                    "type": q.song.type,
                    "position": q.position
                }
                for q in queue
            ]
        }
    except Player.DoesNotExist:
        return {"success": False, "error": "Invalid player token"}
```

## Important Notes

1. **No Migrations**: Since models are `managed = False`, Django won't create/alter tables. The schema is managed by Supabase.
2. **Auth Split**: Django's `User` model is separate from Supabase `profiles`. Only use Django User for admin login.
3. **S3 Uploads**: When admins upload audio in Django, it goes to S3, and the URL is saved to `songs.file_url`.
4. **Read-Only Mostly**: Django primarily reads from Supabase. Node.js handles most writes (votes, preferences).

## Troubleshooting

### "relation does not exist"
- Ensure you've run `DATABASE_SCHEMA.sql` in Supabase first
- Check `DATABASE_URL` is correct

### S3 Upload Fails
- Verify AWS credentials
- Check bucket permissions (public-read for `sounds/` folder)

### Player Token Invalid
- Generate tokens in Django Admin
- Tokens are stored in `players.token` column


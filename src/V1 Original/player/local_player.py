"""
Standalone local audio player - plays local files without backend dependency.
Demonstrates the V1 Original player's crossfade functionality.
"""
import asyncio
import logging
from pathlib import Path
import random
from core import player

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_local_sounds():
    """Get list of all audio files in .audio/ directory."""
    audio_dir = Path(__file__).parent / ".audio"
    if not audio_dir.exists():
        logger.error(f".audio/ directory not found at {audio_dir}")
        return []
    
    files = []
    for ext in ["*.wav", "*.mp3", "*.ogg"]:
        files.extend([f.name for f in audio_dir.glob(ext)])
    
    return files


async def play_local_sounds():
    """Play local sounds with crossfade transitions."""
    sounds = get_local_sounds()
    
    if not sounds:
        logger.error("No audio files found in .audio/ directory!")
        return
    
    logger.info(f"Found {len(sounds)} audio files: {sounds}")
    
    # Play first sound
    first_sound = random.choice(sounds)
    logger.info(f"Starting with: {first_sound}")
    player.play(first_sound, fade_in=True)
    
    # Wait and then crossfade to new sounds every 60 seconds
    await asyncio.sleep(35)  # Let first track play for a bit
    
    while True:
        # Pick a random sound (could be the same one)
        next_sound = random.choice(sounds)
        logger.info(f"Transitioning to: {next_sound}")
        player.transition(next_sound)
        
        # Wait before next transition (30s crossfade + 30s of new track)
        await asyncio.sleep(60)


async def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("V1 Original Audio Player - Local Mode")
    logger.info("Playing local files with 30-second crossfades")
    logger.info("=" * 60)
    
    try:
        await play_local_sounds()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        player.stop()
        logger.info("Player stopped")


if __name__ == "__main__":
    asyncio.run(main())

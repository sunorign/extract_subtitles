"""Wrapper for existing subtitle extraction functionality."""
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add ffmpeg locations to PATH
os.environ["PATH"] = f"{os.path.abspath(project_root)}{os.pathsep}{os.environ['PATH']}"
os.environ["PATH"] = f"{os.path.abspath(project_root)}/ffmpeg-master-latest-win64-gpl-shared/bin{os.pathsep}{os.environ['PATH']}"

logger.info(f"Python PATH set: {os.environ['PATH'][:200]}...")

# Import whisper first
try:
    import whisper
    logger.info("Whisper imported successfully")
except Exception as e:
    logger.exception(f"Failed to import whisper: {e}")
    raise

# Re-import functions from the existing script
from extract_subtitles import (
    FFMPEG,
    FFPROBE,
    check_dependencies,
    has_subtitle_tracks,
    extract_embedded_subtitles,
    transcribe_audio,
)


class ExtractResult:
    def __init__(
        self,
        success: bool,
        subtitle_text: str = "",
        output_path: str = "",
        error: str = "",
    ):
        self.success = success
        self.subtitle_text = subtitle_text
        self.output_path = output_path
        self.error = error


def check_backend_dependencies() -> Tuple[bool, str]:
    """Check if ffmpeg/ffprobe are available."""
    logger.info("Checking backend dependencies...")
    ok = check_dependencies()
    if ok:
        logger.info("All dependencies OK")
        return True, "All dependencies OK"
    else:
        logger.error("ffmpeg/ffprobe check failed")
        return False, "ffmpeg/ffprobe not found"


def process_video(
    video_path: str,
    output_dir: Optional[str],
    whisper_model: str,
    language: Optional[str],
) -> ExtractResult:
    """Process a single video file - extract or transcribe subtitles."""
    logger.info(f"Processing video: {video_path}")
    logger.info(f"Model: {whisper_model}, Language: {language}")

    video_path = Path(video_path)

    # Determine output path
    if output_dir and output_dir.strip():
        output_dir = Path(output_dir.strip())
        output_path = output_dir / f"{video_path.stem}.txt"
    else:
        # Same directory as video
        output_path = video_path.with_suffix(".txt")

    logger.info(f"Output path: {output_path}")

    # Skip if already exists
    if output_path.exists():
        logger.info("Output file already exists, skipping processing")
        with open(output_path, "r", encoding="utf-8") as f:
            text = f.read()
        return ExtractResult(
            success=True,
            subtitle_text=text,
            output_path=str(output_path),
        )

    try:
        has_subs = has_subtitle_tracks(video_path)
        logger.info(f"Video has embedded subtitles: {has_subs}")

        if has_subs:
            logger.info("Extracting embedded subtitles...")
            success = extract_embedded_subtitles(video_path, output_path)
            if not success:
                logger.error("Failed to extract embedded subtitles")
                return ExtractResult(success=False, error="Failed to extract embedded subtitles")
        else:
            logger.info(f"Transcribing audio with Whisper model '{whisper_model}'...")
            success = transcribe_audio(video_path, output_path, whisper_model, language)
            if not success:
                logger.error("Failed to transcribe audio with Whisper")
                return ExtractResult(success=False, error="Failed to transcribe audio with Whisper")
    except Exception as e:
        logger.exception(f"Exception during processing: {e}")
        return ExtractResult(success=False, error=str(e))

    # Read the extracted text
    with open(output_path, "r", encoding="utf-8") as f:
        text = f.read()

    logger.info(f"Extraction successful: {len(text)} characters")

    return ExtractResult(
        success=True,
        subtitle_text=text,
        output_path=str(output_path),
    )

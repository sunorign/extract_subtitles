"""Wrapper for existing subtitle extraction functionality."""
import sys
import os
from pathlib import Path
from typing import Optional, Tuple

# Add project root to Python path
# This is a git worktree - actual project root is two levels up
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add ffmpeg locations to PATH (ffmpeg is in original project root)
original_project_root = project_root.parent.parent
os.environ["PATH"] = f"{os.path.abspath(original_project_root)}{os.pathsep}{os.environ['PATH']}"
os.environ["PATH"] = f"{os.path.abspath(original_project_root)}/ffmpeg-master-latest-win64-gpl-shared/bin{os.pathsep}{os.environ['PATH']}"

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
    # Import whisper here to catch import errors
    try:
        import whisper
        return check_dependencies(), "All dependencies OK"
    except ImportError as e:
        return False, f"Missing Python dependency: {e}"


def process_video(
    video_path: str,
    output_dir: Optional[str],
    whisper_model: str,
    language: Optional[str],
) -> ExtractResult:
    """Process a single video file - extract or transcribe subtitles."""
    video_path = Path(video_path)

    # Determine output path
    if output_dir and output_dir.strip():
        output_dir = Path(output_dir.strip())
        output_path = output_dir / f"{video_path.stem}.txt"
    else:
        # Same directory as video
        output_path = video_path.with_suffix(".txt")

    # Skip if already exists
    if output_path.exists():
        # Read existing and return it
        with open(output_path, "r", encoding="utf-8") as f:
            text = f.read()
        return ExtractResult(
            success=True,
            subtitle_text=text,
            output_path=str(output_path),
        )

    try:
        if has_subtitle_tracks(video_path):
            success = extract_embedded_subtitles(video_path, output_path)
            if not success:
                return ExtractResult(success=False, error="Failed to extract embedded subtitles")
        else:
            success = transcribe_audio(video_path, output_path, whisper_model, language)
            if not success:
                return ExtractResult(success=False, error="Failed to transcribe audio with Whisper")
    except Exception as e:
        return ExtractResult(success=False, error=str(e))

    # Read the extracted text
    with open(output_path, "r", encoding="utf-8") as f:
        text = f.read()

    return ExtractResult(
        success=True,
        subtitle_text=text,
        output_path=str(output_path),
    )

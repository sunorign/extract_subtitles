#!/usr/bin/env python3
"""Extract subtitles from MP4 files in current directory."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract subtitles from MP4 files (extract embedded or transcribe with Whisper)"
    )
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code (auto-detected if not specified)",
    )
    args = parser.parse_args()
    return args


def check_dependencies():
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("[OK] ffmpeg found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] ffmpeg not found in PATH")
        print("\nPlease install ffmpeg first:")
        print("  - Windows: choco install ffmpeg (via Chocolatey)")
        print("  - macOS: brew install ffmpeg")
        print("  - Ubuntu/Debian: sudo apt install ffmpeg")
        return False


def has_subtitle_tracks(video_path: Path) -> bool:
    """Check if video file has any embedded subtitle tracks."""
    # Use ffprobe to list streams
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # If any output, there are subtitle streams
    return bool(result.stdout.strip())


def main():
    args = parse_args()
    if not check_dependencies():
        sys.exit(1)
    print(f"Looking for MP4 files in current directory...")
    mp4_files = list(Path(".").glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 file(s)")
    for video in mp4_files:
        has_sub = has_subtitle_tracks(video)
        print(f"  {video.name}: has_subtitles={has_sub}")
    # Import whisper here so help works even if whisper not installed
    global whisper
    import whisper


if __name__ == "__main__":
    main()

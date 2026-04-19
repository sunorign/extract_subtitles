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


def main():
    args = parse_args()
    if not check_dependencies():
        sys.exit(1)
    print(f"Looking for MP4 files in current directory...")
    mp4_files = list(Path(".").glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 file(s)")
    # Import whisper here so help works even if whisper not installed
    global whisper
    import whisper


if __name__ == "__main__":
    main()

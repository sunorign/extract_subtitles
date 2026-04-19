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


def main():
    args = parse_args()
    # Import whisper here so help works even if whisper not installed
    global whisper
    import whisper
    print(f"Looking for MP4 files in current directory...")
    mp4_files = list(Path(".").glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 file(s)")


if __name__ == "__main__":
    main()

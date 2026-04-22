#!/usr/bin/env python3
"""Extract subtitles from MP4 files in current directory."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Import whisper for audio transcription
import whisper

# Add current directory to PATH so whisper can find ffmpeg/ffprobe
os.environ["PATH"] = f"{os.path.abspath('.')}{os.pathsep}{os.environ['PATH']}"
# Also add the download bin directory to PATH
os.environ["PATH"] = f"{os.path.abspath('.')}/ffmpeg-master-latest-win64-gpl-shared/bin{os.pathsep}{os.environ['PATH']}"

# Find ffmpeg and ffprobe - check PATH then current directory
def find_ffmpeg(name: str) -> str:
    """Find ffmpeg/ffprobe executable, check PATH then current directory."""
    # First check if it's in PATH
    try:
        result = subprocess.run(
            [name, "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        return name
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Check current directory for .exe
    exe_name = f"{name}.exe"
    exe_path = Path(exe_name).absolute()
    if exe_path.exists():
        return str(exe_path)

    # Check in ffmpeg/bin subdirectory
    ffmpeg_bin_exe = Path(f"ffmpeg/bin/{exe_name}").absolute()
    if ffmpeg_bin_exe.exists():
        return str(ffmpeg_bin_exe)

    # Check downloaded ffmpeg-master-latest-win64-gpl-shared/bin
    ffmpeg_dl_exe = Path(f"ffmpeg-master-latest-win64-gpl-shared/bin/{exe_name}").absolute()
    if ffmpeg_dl_exe.exists():
        return str(ffmpeg_dl_exe)

    return name


FFMPEG = find_ffmpeg("ffmpeg")
FFPROBE = find_ffmpeg("ffprobe")


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
    # Try direct first
    try:
        result = subprocess.run(
            [FFMPEG, "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[OK] ffmpeg found at {FFMPEG}")
        # Also check ffprobe
        result = subprocess.run(
            [FFPROBE, "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[OK] ffprobe found at {FFPROBE}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try with shell=True for Git Bash / MSYS2 environments
        try:
            result = subprocess.run(
                f"{FFMPEG} -version",
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            print(f"[OK] ffmpeg found at {FFMPEG}")
            result = subprocess.run(
                f"{FFPROBE} -version",
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            print(f"[OK] ffprobe found at {FFPROBE}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] ffmpeg/ffprobe not found")
            print("\nPlease install ffmpeg:")
            print("  1. Download from: https://github.com/BtbN/FFmpeg-Builds/releases")
            print("  2. Download ffmpeg-master-latest-win64-gpl.zip")
            print("  3. Extract ffmpeg.exe and ffprobe.exe to this directory")
            print("  Or install via package manager:")
            print("  - Windows (Chocolatey): choco install ffmpeg")
            print("  - Windows (winget): winget install ffmpeg")
            print("  - macOS: brew install ffmpeg")
            print("  - Ubuntu/Debian: sudo apt install ffmpeg")
            return False


def has_subtitle_tracks(video_path: Path) -> bool:
    """Check if video file has any embedded subtitle tracks."""
    # Use ffprobe to list streams
    cmd = [
        FFPROBE,
        "-v", "error",
        "-select_streams", "s",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except (FileNotFoundError):
        # Retry with shell=True for MSYS2/Git Bash
        cmd_str = " ".join([FFPROBE, "-v", "error", "-select_streams", "s", "-show_entries", "stream=codec_type", "-of", "default=noprint_wrappers=1", str(video_path)])
        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)
    # If any output, there are subtitle streams
    return bool(result.stdout.strip())


def extract_embedded_subtitles(video_path: Path, output_path: Path) -> bool:
    """Extract first subtitle track and convert to plain text."""
    # Extract to .srt first
    temp_srt = video_path.with_suffix(".srt")
    cmd = [
        FFMPEG,
        "-y",
        "-i", str(video_path),
        "-map", "0:s:0",  # First subtitle stream
        "-c", "copy",
        str(temp_srt),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        # Retry with shell=True for MSYS2/Git Bash
        cmd_str = " ".join([FFMPEG, "-y", "-i", f'"{str(video_path)}"', "-map", "0:s:0", "-c", "copy", f'"{str(temp_srt)}"'])
        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"  Failed to extract subtitles: {result.stderr}")
        return False

    # Convert SRT to plain text
    with open(temp_srt, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    text = []
    for line in lines:
        line = line.strip()
        # Skip line numbers, timestamps, and empty lines
        if not line or line.isdigit() or "-->" in line:
            continue
        text.append(line)

    # Join into single text block
    plain_text = " ".join(text)

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(plain_text)

    # Clean up temp .srt
    os.remove(temp_srt)

    print(f"  Extracted embedded subtitles to {output_path.name}")
    return True


def transcribe_audio(video_path: Path, output_path: Path, model_name: str, language: str | None) -> bool:
    """Transcribe audio from video using OpenAI Whisper."""
    print(f"  Loading Whisper model '{model_name}'...")
    try:
        model = whisper.load_model(model_name)
        print(f"  Transcribing audio... (this may take a while)")
        result = model.transcribe(
            str(video_path),
            language=language,
            verbose=False,
        )

        # Write plain text
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"].strip())

        print(f"  Transcription saved to {output_path.name}")
        return True
    except Exception as e:
        print(f"  Failed to transcribe audio: {e}")
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

    for video in mp4_files:
        print(f"\nProcessing: {video.name}")
        output_path = video.with_suffix(".txt")
        if output_path.exists():
            print(f"  Output already exists, skipping")
            continue

        if has_subtitle_tracks(video):
            print(f"  Found embedded subtitles, extracting...")
            success = extract_embedded_subtitles(video, output_path)
        else:
            print(f"  No embedded subtitles found, transcribing with Whisper...")
            success = transcribe_audio(video, output_path, args.model, args.language)

        if not success:
            print(f"  Failed to process {video.name}")


if __name__ == "__main__":
    main()

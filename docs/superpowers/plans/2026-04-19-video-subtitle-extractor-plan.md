# Video Subtitle Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a script that extracts subtitles from all MP4 videos in current directory - extracts embedded subtitles if present, generates via OpenAI Whisper if not.

**Architecture:** Single Python script that scans the current directory, processes each video in sequence. Uses FFmpeg for subtitle extraction/audio extraction and OpenAI Whisper for speech-to-text. No complex configuration needed.

**Tech Stack:** Python 3, FFmpeg (system command), OpenAI Whisper (Python package).

---

## File Structure

- Create: `extract_subtitles.py` - Main script with all functionality
- Output: `<video>.txt` - One text file per input video (created in same directory)

---

### Task 1: Create script skeleton with argument parsing

**Files:**
- Create: `extract_subtitles.py`

- [ ] **Step 1: Write initial script structure**

```python
#!/usr/bin/env python3
"""Extract subtitles from MP4 files in current directory."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import whisper


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
    print(f"Looking for MP4 files in current directory...")
    mp4_files = list(Path(".").glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 file(s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run script to verify it works**

Run: `python extract_subtitles.py --help`
Expected: Shows help message

- [ ] **Step 3: Commit**

```bash
git add extract_subtitles.py docs/superpowers/plans/2026-04-19-video-subtitle-extractor-plan.md
git commit -m "feat: add initial script skeleton"
```

---

### Task 2: Add dependency check (ffmpeg availability)

**Files:**
- Modify: `extract_subtitles.py`

- [ ] **Step 1: Add dependency checking function**

Add after `parse_args()` before `main()`:

```python
def check_dependencies():
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ ffmpeg found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ffmpeg not found in PATH")
        print("\nPlease install ffmpeg first:")
        print("  - Windows: choco install ffmpeg (via Chocolatey)")
        print("  - macOS: brew install ffmpeg")
        print("  - Ubuntu/Debian: sudo apt install ffmpeg")
        return False
```

Update `main()`:

```python
def main():
    args = parse_args()
    if not check_dependencies():
        sys.exit(1)
    print(f"Looking for MP4 files in current directory...")
    mp4_files = list(Path(".").glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 file(s)")
```

- [ ] **Step 2: Test dependency check**

Run: `python extract_subtitles.py`
Expected: Shows "✓ ffmpeg found" (if installed) or installation instructions

- [ ] **Step 3: Commit**

```bash
git add extract_subtitles.py
git commit -m "feat: add ffmpeg dependency check"
```

---

### Task 3: Add function to check for existing subtitle tracks

**Files:**
- Modify: `extract_subtitles.py`

- [ ] **Step 1: Add function to detect subtitle tracks**

Add after `check_dependencies()`:

```python
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
```

- [ ] **Step 2: Test detection on existing files**

Add test code temporarily in `main()` after `print(f"Found {len(mp4_files)} MP4 file(s)")`:

```python
for video in mp4_files:
    has_sub = has_subtitle_tracks(video)
    print(f"  {video.name}: has_subtitles={has_sub}")
```

Run: `python extract_subtitles.py`
Expected: Lists whether each file has subtitles

- [ ] **Step 3: Commit**

```bash
git add extract_subtitles.py
git commit -m "feat: add subtitle track detection"
```

---

### Task 4: Add embedded subtitle extraction to text

**Files:**
- Modify: `extract_subtitles.py`

- [ ] **Step 1: Add subtitle extraction and conversion function**

Add after `has_subtitle_tracks()`:

```python
def extract_embedded_subtitles(video_path: Path, output_path: Path) -> bool:
    """Extract first subtitle track and convert to plain text."""
    # Extract to .srt first
    temp_srt = video_path.with_suffix(".srt")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-map", "0:s:0",  # First subtitle stream
        "-c", "copy",
        str(temp_srt),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
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
```

- [ ] **Step 2: Test extraction (if any video has subtitles)**

Update `main()` after printing MP4 count:

```python
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
        print(f"  No embedded subtitles found, will transcribe later...")
```

Run: `python extract_subtitles.py`
Expected: Processes each file, extracts if subtitles found

- [ ] **Step 3: Commit**

```bash
git add extract_subtitles.py
git commit -m "feat: add embedded subtitle extraction"
```

---

### Task 5: Add Whisper transcription function

**Files:**
- Modify: `extract_subtitles.py`

- [ ] **Step 1: Add transcription function**

Add after `extract_embedded_subtitles()`:

```python
def transcribe_audio(video_path: Path, output_path: Path, model_name: str, language: str | None) -> bool:
    """Transcribe audio from video using OpenAI Whisper."""
    print(f"  Loading Whisper model '{model_name}'...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print(f"  Failed to load Whisper model: {e}")
        return False

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
```

- [ ] **Step 2: Update main() to handle transcription**

Update the processing loop in `main()`:

```python
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
```

- [ ] **Step 3: Test transcription**

Run: `python extract_subtitles.py --model base`
Expected: Downloads model on first run, then transcribes any videos without embedded subtitles

- [ ] **Step 4: Commit**

```bash
git add extract_subtitles.py
git commit -m "feat: add whisper transcription support"
```

---

### Task 6: Final testing and verification

**Files:**
- Read and verify: `extract_subtitles.py`

- [ ] **Step 1: Run full batch processing**

Run: `python extract_subtitles.py`
Expected: All MP4 files in directory get processed to .txt files

- [ ] **Step 2: Verify output text files**

Check that `.txt` files were created and contain text:

```bash
ls -la *.txt
cat "your-output-file.txt" | head -20
```

- [ ] **Step 3: Commit any final cleanups (if needed)**

```bash
git add extract_subtitles.py
git commit -m "refactor: final cleanup"
```

---

## Self-Review

- **Spec coverage:** ✓ All requirements covered - embedded extraction, Whisper transcription, batch processing, .txt output
- **Placeholders:** ✓ No TBD/placeholders, all code shown
- **Consistency:** ✓ Function names and signatures consistent throughout

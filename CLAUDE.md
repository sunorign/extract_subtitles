# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a Python script for batch extracting subtitles from MP4 video files. If a video has embedded subtitles, they are extracted directly. If not, audio is transcribed using OpenAI Whisper (speech-to-text) to generate a text file.

## Commands

### Run the script
```bash
python extract_subtitles.py
```

### Run with custom Whisper model
```bash
python extract_subtitles.py --model {tiny|base|small|medium|large}
```

### Run with specified language
```bash
python extract_subtitles.py --language zh
```

## Architecture

### Files

- `extract_subtitles.py` - Main script, single-file implementation with the following structure:
  1. `find_ffmpeg(name)` - Find ffmpeg/ffprobe (checks PATH, current directory, and downloaded bin directory)
  2. `check_dependencies()` - Verify ffmpeg/ffprobe are available
  3. `has_subtitle_tracks(video_path)` - Detect if video has embedded subtitle streams using ffprobe
  4. `extract_embedded_subtitles(video_path, output_path)` - Extract SRT and convert to plain text
  5. `transcribe_audio(video_path, output_path, model_name, language)` - Transcribe audio using OpenAI Whisper
  6. `main()` - Orchestrate processing of all MP4 files in current directory

### Behavior

- Skips output files that already exist (idempotent)
- If embedded subtitles exist → extract directly to `.txt`
- If no embedded subtitles → transcribe audio with Whisper → save to `.txt`
- Output: One `.txt` file per `.mp4` video with the same base name

### Dependencies

- System: `ffmpeg` and `ffprobe` (included in this directory)
- Python: `openai-whisper` (install via `pip install openai-whisper`)

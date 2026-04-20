# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-file Python tool for batch subtitle extraction from MP4 videos:
- Extracts embedded subtitles directly if present
- Falls back to OpenAI Whisper speech-to-text when no embedded subtitles exist
- Saves output as `.txt` file with the same name as the input video

## Commands

```bash
# Run on all MP4 files in current directory
python extract_subtitles.py

# Use specific Whisper model size
python extract_subtitles.py --model {tiny,base,small,medium,large}

# Specify language (avoids auto-detection)
python extract_subtitles.py --language zh
```

## Architecture

This is a single-file implementation (`extract_subtitles.py`):

1. **Finding ffmpeg**: `find_ffmpeg(name)` - Checks PATH, current directory, and `ffmpeg-master-latest-win64-gpl-shared/bin/` for the executable
2. **Dependency checking**: `check_dependencies()` - Verifies ffmpeg/ffprobe are available before proceeding
3. **Subtitle detection**: `has_subtitle_tracks(video_path)` - Uses ffprobe to check for embedded subtitle streams
4. **Extraction**: `extract_embedded_subtitles(video_path, output_path)` - Extracts SRT and converts to plain text
5. **Transcription**: `transcribe_audio(video_path, output_path, model_name, language)` - Uses Whisper to transcribe audio to text
6. **Orchestration**: `main()` - Iterates all `.mp4` files, skips existing outputs, routes to extraction or transcription

## Key Behavior

- Idempotent: Skips output files that already exist
- Works offline after initial Whisper model download
- Automatically adds current directory to PATH so Whisper can find ffmpeg
- Output: One `.txt` file per input `.mp4` in the same directory

## Dependencies

- System requirement: `ffmpeg` and `ffprobe` (included in this repository)
- Python package: `openai-whisper` (install with `pip install openai-whisper`)

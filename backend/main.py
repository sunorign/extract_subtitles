"""FastAPI backend server for subtitle extraction GUI."""
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List

# Add backend directory to Python path FIRST (before imports)
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
print(f"Added to Python path: {backend_dir}")

# Also add backend's parent (gui-dev/) to find extract_subtitles.py
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
print(f"Added to Python path: {project_root}")

# Add ffmpeg locations to PATH
os.environ["PATH"] = f"{os.path.abspath(project_root)}{os.pathsep}{os.environ['PATH']}"
os.environ["PATH"] = f"{os.path.abspath(project_root)}/ffmpeg-master-latest-win64-gpl-shared/bin{os.pathsep}{os.environ['PATH']}"
print(f"Python PATH env: {os.environ['PATH'][:200]}")

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

from subtitle_extractor import (
    check_backend_dependencies,
    process_video,
    ExtractResult,
)
from ai_summarizer import (
    AIConfig,
    summarize_subtitle,
    test_connection,
    AIResult,
)


app = FastAPI(title="Subtitle Extractor Backend", version="1.0.0")


# === Pydantic Models ===

class AIConfigRequest(BaseModel):
    api_url: str = Field(..., description="API endpoint URL")
    model: str = Field(..., description="Model name")
    api_key: str = Field(..., description="API key")
    prompt_template: str = Field(..., description="Prompt template for summarization")


class ProcessRequest(BaseModel):
    video_path: str = Field(..., description="Path to input video file")
    output_dir: Optional[str] = Field(None, description="Output directory, None = same as video")
    whisper_model: str = Field(default="base", description="Whisper model name")
    language: Optional[str] = Field(None, description="Language code, None = auto-detect")
    enable_ai: bool = Field(default=False, description="Whether to enable AI summarization")
    ai_config: Optional[AIConfigRequest] = Field(None, description="AI configuration if enable_ai is true")


class ProcessResponse(BaseModel):
    success: bool
    subtitle_path: Optional[str] = None
    summary_path: Optional[str] = None
    subtitle_text: Optional[str] = None
    summary_text: Optional[str] = None
    message: str = ""


class TestAIRequest(BaseModel):
    ai_config: AIConfigRequest


class TestAIResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    healthy: bool
    message: str


# === Endpoints ===

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    logger.info("Health check requested")
    ok, msg = check_backend_dependencies()
    logger.info(f"Health check result: {ok} - {msg}")
    return HealthResponse(healthy=ok, message=msg)


@app.post("/test-ai", response_model=TestAIResponse)
def test_ai(req: TestAIRequest):
    """Test AI connection with given configuration."""
    config = AIConfig(
        api_url=req.ai_config.api_url,
        model=req.ai_config.model,
        api_key=req.ai_config.api_key,
        prompt_template=req.ai_config.prompt_template,
    )
    result = test_connection(config)
    if result.success:
        return TestAIResponse(success=True, message=f"Connection OK: {result.content}")
    else:
        raise HTTPException(status_code=400, detail=result.error)


@app.post("/process", response_model=ProcessResponse)
def process(req: ProcessRequest):
    """Process a single video file - extract subtitle and optionally summarize."""
    logger.info(f"Processing request received: video={req.video_path}, model={req.whisper_model}, lang={req.language}, ai={req.enable_ai}")

    # Validate video exists
    video_path = Path(req.video_path)
    if not video_path.exists():
        logger.error(f"Video file not found: {req.video_path}")
        raise HTTPException(status_code=404, detail=f"Video file not found: {req.video_path}")

    logger.info(f"Video file exists, size: {video_path.stat().st_size} bytes")

    # Extract subtitle
    try:
        result: ExtractResult = process_video(
            video_path=str(video_path),
            output_dir=req.output_dir,
            whisper_model=req.whisper_model,
            language=req.language,
        )
    except Exception as e:
        logger.exception(f"Exception during subtitle extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    if not result.success:
        logger.error(f"Subtitle extraction failed: {result.error}")
        raise HTTPException(status_code=500, detail=result.error)

    logger.info(f"Subtitle extracted successfully: {len(result.subtitle_text)} characters")

    response = ProcessResponse(
        success=True,
        subtitle_path=result.output_path,
        subtitle_text=result.subtitle_text,
        message="Subtitle extracted successfully",
    )

    # Do AI summarization if enabled
    if req.enable_ai and req.ai_config:
        logger.info("Starting AI summarization")
        ai_config = AIConfig(
            api_url=req.ai_config.api_url,
            model=req.ai_config.model,
            api_key=req.ai_config.api_key,
            prompt_template=req.ai_config.prompt_template,
        )
        try:
            ai_result = summarize_subtitle(result.subtitle_text, ai_config)
        except Exception as e:
            logger.exception(f"Exception during AI summarization: {e}")
            raise HTTPException(status_code=500, detail=f"AI internal error: {str(e)}")

        if ai_result.success:
            logger.info("AI summarization succeeded")
            # Save summary to file
            output_path = Path(result.output_path)
            summary_path = output_path.with_name(f"{output_path.stem}_summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(ai_result.content)
            response.summary_path = str(summary_path)
            response.summary_text = ai_result.content
        else:
            logger.error(f"AI summarization failed: {ai_result.error}")
            raise HTTPException(status_code=500, detail=f"AI summarization failed: {ai_result.error}")

    logger.info("Processing completed successfully")
    return response


def start_server(port: int = 8765):
    """Start the uvicorn server."""
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Starting server on port {port}")
    start_server(port)

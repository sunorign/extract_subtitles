"""FastAPI backend server for subtitle extraction GUI."""
import sys
import os
from pathlib import Path
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add current directory and ffmpeg locations to PATH
# The actual project root is two levels up (this is a git worktree)
original_project_root = project_root.parent.parent
os.environ["PATH"] = f"{os.path.abspath(original_project_root)}{os.pathsep}{os.environ['PATH']}"
os.environ["PATH"] = f"{os.path.abspath(original_project_root)}/ffmpeg-master-latest-win64-gpl-shared/bin{os.pathsep}{os.environ['PATH']}"


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
    ok, msg = check_backend_dependencies()
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
    # Validate video exists
    video_path = Path(req.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video file not found: {req.video_path}")

    # Extract subtitle
    result: ExtractResult = process_video(
        video_path=str(video_path),
        output_dir=req.output_dir,
        whisper_model=req.whisper_model,
        language=req.language,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    response = ProcessResponse(
        success=True,
        subtitle_path=result.output_path,
        subtitle_text=result.subtitle_text,
        message="Subtitle extracted successfully",
    )

    # Do AI summarization if enabled
    if req.enable_ai and req.ai_config:
        ai_config = AIConfig(
            api_url=req.ai_config.api_url,
            model=req.ai_config.model,
            api_key=req.ai_config.api_key,
            prompt_template=req.ai_config.prompt_template,
        )
        ai_result = summarize_subtitle(result.subtitle_text, ai_config)
        if ai_result.success:
            # Save summary to file
            output_path = Path(result.output_path)
            summary_path = output_path.with_name(f"{output_path.stem}_summary.md")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(ai_result.content)
            response.summary_path = str(summary_path)
            response.summary_text = ai_result.content
        else:
            raise HTTPException(status_code=500, detail=f"AI summarization failed: {ai_result.error}")

    return response


def start_server(port: int = 8765):
    """Start the uvicorn server."""
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    start_server()

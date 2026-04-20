"""AI summarization supporting OpenAI-compatible and Anthropic APIs."""
from typing import Optional, Dict, Any
import requests
import json


class AIConfig:
    def __init__(
        self,
        api_url: str,
        model: str,
        api_key: str,
        prompt_template: str,
    ):
        self.api_url = api_url
        self.model = model
        self.api_key = api_key
        self.prompt_template = prompt_template


class AIResult:
    def __init__(self, success: bool, content: str = "", error: str = ""):
        self.success = success
        self.content = content
        self.error = error


def summarize_subtitle(
    subtitle_text: str,
    config: AIConfig,
) -> AIResult:
    """Summarize subtitle text using configured AI API."""

    # Build the full prompt
    prompt = f"{config.prompt_template}\n\n{subtitle_text}"

    # Detect if this is Anthropic API (contains /messages in URL)
    is_anthropic = "/messages" in config.api_url and "anthropic" in config.api_url

    try:
        if is_anthropic:
            return _call_anthropic(prompt, config)
        else:
            return _call_openai_compatible(prompt, config)
    except Exception as e:
        return AIResult(success=False, error=str(e))


def test_connection(config: AIConfig) -> AIResult:
    """Test if AI connection works with a simple request."""
    test_prompt = "Say 'Hello, this is a test message.' in one short sentence."
    test_config = AIConfig(
        api_url=config.api_url,
        model=config.model,
        api_key=config.api_key,
        prompt_template=test_prompt,
    )
    return summarize_subtitle("", test_config)


def _call_openai_compatible(prompt: str, config: AIConfig) -> AIResult:
    """Call OpenAI-compatible API (OpenAI, compatible endpoints)."""
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
    }

    response = requests.post(
        config.api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code != 200:
        return AIResult(
            success=False,
            error=f"HTTP {response.status_code}: {response.text}",
        )

    data = response.json()

    if "choices" not in data or len(data["choices"]) == 0:
        return AIResult(
            success=False,
            error=f"Unexpected response format: {json.dumps(data)}",
        )

    content = data["choices"][0]["message"]["content"].strip()
    return AIResult(success=True, content=content)


def _call_anthropic(prompt: str, config: AIConfig) -> AIResult:
    """Call Anthropic Claude API."""
    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.7,
    }

    response = requests.post(
        config.api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code != 200:
        return AIResult(
            success=False,
            error=f"HTTP {response.status_code}: {response.text}",
        )

    data = response.json()

    if "content" not in data or len(data["content"]) == 0:
        return AIResult(
            success=False,
            error=f"Unexpected response format: {json.dumps(data)}",
        )

    # Anthropic returns content blocks, find the text one
    for block in data["content"]:
        if block.get("type") == "text":
            content = block["text"].strip()
            return AIResult(success=True, content=content)

    return AIResult(
        success=False,
        error="No text content in response",
    )

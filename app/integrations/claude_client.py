from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import get_settings

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "summary_v1.txt"


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


class ClaudeClient:
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def complete(self, user_text: str) -> dict[str, Any]:
        body = {
            "model": self.model,
            "max_tokens": 2048,
            "system": load_system_prompt(),
            "messages": [
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=body,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Falha ao contatar o Claude: {exc}",
            ) from exc

        if response.status_code in {401, 403}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credenciais do Claude inválidas ou sem permissão.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Claude retornou HTTP {response.status_code}.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude retornou uma resposta inválida.",
            ) from exc

        text = _extract_text(payload)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude não retornou texto utilizável.",
            )
        return {"model": self.model, "text": text, "raw": payload}


def _extract_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for block in payload.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            chunks.append(str(block.get("text") or ""))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def get_claude_client() -> ClaudeClient:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ANTHROPIC_API_KEY não está configurado.",
        )
    return ClaudeClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        timeout=settings.request_timeout_seconds,
    )

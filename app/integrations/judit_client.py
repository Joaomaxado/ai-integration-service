import asyncio
import json
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import get_settings

PENDING_STATUSES = {"pending", "started", "processing"}


class JuditClient:
    def __init__(self, base_url: str, api_key: str, timeout: float, poll_interval: float):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.poll_interval = poll_interval

    def _headers(self) -> dict[str, str]:
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Falha ao contatar a Judit: {exc}",
            ) from exc

        if response.status_code in {401, 403}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credenciais da Judit inválidas ou sem permissão.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Judit retornou HTTP {response.status_code}.",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Judit retornou uma resposta inválida.",
            ) from exc

        if not isinstance(payload, dict):
            return {"data": payload}
        return payload

    async def create_cnj_request(self, cnj: str) -> dict[str, Any]:
        payload = {
            "search": {
                "search_type": "lawsuit_cnj",
                "search_key": cnj,
                "search_params": {"full_lawsuit": True},
            }
        }
        return await self._request("POST", "/requests", json=payload)

    async def get_request(self, request_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/requests/{request_id}")

    async def get_responses(self, request_id: str, page: int = 1) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/responses",
            params={"request_id": request_id, "page": page, "page_size": 50},
        )

    async def wait_until_complete(self, request_id: str) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.timeout
        current = await self.get_request(request_id)
        while current.get("status") in PENDING_STATUSES:
            if asyncio.get_running_loop().time() >= deadline:
                return current
            await asyncio.sleep(self.poll_interval)
            current = await self.get_request(request_id)
        return current

    async def consult_by_cnj(self, cnj: str, wait_for_result: bool = True) -> dict[str, Any]:
        created = await self.create_cnj_request(cnj)
        request_id = created.get("request_id")
        if not request_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Judit não retornou request_id.",
            )

        request_data = created
        responses = None
        if wait_for_result:
            request_data = await self.wait_until_complete(request_id)
            if request_data.get("status") == "completed":
                responses = await self.get_responses(request_id)

        return {
            "request_id": request_id,
            "status": request_data.get("status", "pending"),
            "cnj": cnj,
            "request": request_data,
            "data": responses,
        }


def get_judit_client() -> JuditClient:
    settings = get_settings()
    if not settings.judit_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JUDIT_API_KEY não está configurado.",
        )
    return JuditClient(
        base_url=settings.judit_requests_base_url,
        api_key=settings.judit_api_key,
        timeout=settings.request_timeout_seconds,
        poll_interval=settings.judit_poll_interval_seconds,
    )


def responses_to_text(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""

    items = payload.get("page_data")
    if not items:
        return json.dumps(payload, ensure_ascii=False)[:40_000]

    parts: list[str] = []
    for item in items:
        data = item.get("response_data") if isinstance(item, dict) else item
        if isinstance(data, dict):
            steps = data.get("steps") or data.get("movements") or []
            cover = {key: value for key, value in data.items() if key not in {"steps", "movements", "attachments"}}
            parts.append(json.dumps(cover, ensure_ascii=False, indent=2))
            for step in steps[:80]:
                parts.append(json.dumps(step, ensure_ascii=False))
        else:
            parts.append(json.dumps(data, ensure_ascii=False))
    return "\n\n".join(parts)[:40_000]

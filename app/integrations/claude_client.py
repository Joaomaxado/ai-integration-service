from app.config import get_settings


class ClaudeClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY não configurada")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise RuntimeError("Dependência anthropic não instalada") from exc
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def complete(self, text: str) -> dict[str, str]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1800,
            system="Responda em português brasileiro seguindo o formato solicitado.",
            messages=[{'role': 'user', 'content': text}],
        )

        text_blocks = [
            block.text for block in response.content
            if getattr(block, 'type', None) == 'text'
        ]
        if not text_blocks:
            raise RuntimeError("Claude retornou uma resposta sem texto")
        return {"text": "\n".join(text_blocks), "model": self.model}

    async def generate(self, *, system: str, user_text: str) -> str:
        result = await self.complete(f"{system}\n\n{user_text}")
        return result["text"]


ClaudeCliente = ClaudeClient


def get_claude_client() -> ClaudeClient:
    return ClaudeClient()
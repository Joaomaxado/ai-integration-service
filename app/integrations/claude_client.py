import os
from anthropic import AsyncAnthropic

class ClaudeCliente:
    def __init__(self) -> None:
        api_key = os.environ['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']
        self.client = AsyncAnthropic(api_key= api_key)
        self.model = os.environ['claude-3-5-sonnet-20241022']

    async def generate(self, *, system: str, user_text: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1800,
            system=system,
            messages=[{'role': 'user', 'content': user_text}],
        )

        text_blocks = [
            block.text for block in response.content
            if getattr(block, 'type', None) == 'text'
        ]
        if not text_blocks:
            raise RuntimeError('Claude retornou uma resposta sem text')
        return '\n'.join(text_blocks)
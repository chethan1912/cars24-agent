import anthropic
from core.config import settings


class LLMService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def complete_haiku(self, prompt: str, max_tokens: int = 300) -> str:
        """Fast, cheap. Use for: intent classification, constraint change detection, context patching."""
        message = self.client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def complete_sonnet(self, prompt: str, max_tokens: int = 1000) -> str:
        """Higher quality. Use for: final ranking, response generation, complex reasoning."""
        message = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def stream_sonnet(self, system: str, messages: list[dict]):
        """Streaming response for real-time UX. Use for final user-facing response generation."""
        with self.client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text

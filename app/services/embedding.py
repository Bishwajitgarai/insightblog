from abc import ABC, abstractmethod
from typing import List
import openai
from app.core.config import get_settings

settings = get_settings()

class EmbeddingService(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass

class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    async def embed_text(self, text: str) -> List[float]:
        # In a real app, handle async properly or use async client
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding

class MockEmbeddingService(EmbeddingService):
    async def embed_text(self, text: str) -> List[float]:
        # Return a random vector of size 1536 (Ada-002 size)
        import random
        return [random.random() for _ in range(1536)]

def get_embedding_service() -> EmbeddingService:
    if settings.OPENAI_API_KEY == "sk-placeholder":
        return MockEmbeddingService()
    return OpenAIEmbeddingService()

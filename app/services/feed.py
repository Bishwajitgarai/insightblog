from typing import List
from app.services.vespa_app import vespa_service
from app.services.embedding import get_embedding_service
from app.models.domain import ContentItem

class FeedService:
    def __init__(self):
        self.vespa = vespa_service
        self.embedding_service = get_embedding_service()

    async def get_feed_for_user(self, user_id: str, user_interests: str) -> List[ContentItem]:
        # 1. Generate embedding for user interests
        # In a real app, we might fetch the user profile from Redis/DB first
        user_embedding = await self.embedding_service.embed_text(user_interests)

        # 2. Query Vespa
        results = await self.vespa.query_content(user_embedding)

        # 3. Parse results
        items = []
        for res in results:
            fields = res.get("fields", {})
            items.append(ContentItem(
                content_id=res.get("id", "unknown"),
                title=fields.get("title", "No Title"),
                body=fields.get("body", ""),
                tags=[], # Populate if available
                embedding=None # Don't return embedding to client usually
            ))
        return items

    async def ingest_content(self, content: ContentItem):
        # 1. Generate embedding
        text_to_embed = f"{content.title} {content.body}"
        embedding = await self.embedding_service.embed_text(text_to_embed)
        content.embedding = embedding

        # 2. Feed to Vespa
        await self.vespa.feed_content(content.content_id, {
            "title": content.title,
            "body": content.body,
            "embedding": embedding
        })
        return content

feed_service = FeedService()

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

# Redis connection pool
redis_client = None

async def get_redis():
    """Get Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

class NotificationBroadcaster:
    """Broadcast notifications via Redis pub/sub"""
    
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await get_redis()
    
    async def publish_notification(self, user_id: int, notification_data: dict):
        """Publish notification to user's channel"""
        if not self.redis:
            await self.connect()
        
        channel = f"notifications:{user_id}"
        await self.redis.publish(channel, str(notification_data))
    
    async def subscribe_to_notifications(self, user_id: int):
        """Subscribe to user's notification channel"""
        if not self.redis:
            await self.connect()
        
        pubsub = self.redis.pubsub()
        channel = f"notifications:{user_id}"
        await pubsub.subscribe(channel)
        return pubsub

# Global broadcaster instance
broadcaster = NotificationBroadcaster()

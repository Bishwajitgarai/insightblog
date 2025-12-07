from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
import json
import asyncio

from app.services.redis_service import broadcaster
from app.api.v1.endpoints.users import get_current_user
from app.models.user import User

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications"""
    
    # Get token from query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    
    # Validate token and get user
    try:
        from jose import jwt
        from app.core.config import get_settings
        settings = get_settings()
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            await websocket.close(code=1008)
            return
        
        # Get user from database
        from app.db.session import get_session
        from sqlalchemy import select
        
        async for session in get_session():
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalars().first()
            
            if not user:
                await websocket.close(code=1008)
                return
            
            user_id = user.id
            break
        
    except Exception as e:
        await websocket.close(code=1008)
        return
    
    # Connect WebSocket
    await manager.connect(websocket, user_id)
    
    # Subscribe to Redis notifications
    pubsub = await broadcaster.subscribe_to_notifications(user_id)
    
    try:
        # Listen for messages
        while True:
            # Check for Redis messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['type'] == 'message':
                # Send notification to WebSocket client
                await websocket.send_text(message['data'])
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await pubsub.unsubscribe()
        await pubsub.close()
    except Exception as e:
        manager.disconnect(user_id)
        await pubsub.unsubscribe()
        await pubsub.close()

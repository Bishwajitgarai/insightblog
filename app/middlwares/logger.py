import time
import uuid
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging import logger
from app.core.context import request_id_context

# Context variable to store request ID
# request_id_context is now imported from app.core.context

class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate Request ID
        request_id = str(uuid.uuid4())
        request_id_context.set(request_id)
        
        # Start Timer
        start_time = time.time()
        
        # Process Request
        response = await call_next(request)
        
        # Calculate Duration
        process_time = time.time() - start_time
        
        # Add Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(f"Request: {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.4f}s")
        
        return response

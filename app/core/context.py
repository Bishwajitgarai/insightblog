from contextvars import ContextVar

# Context variable to store request ID
request_id_context: ContextVar[str] = ContextVar("request_id", default="N/A")

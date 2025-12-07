import random
import string
from app.core.redis import redis_client
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

OTP_EXPIRY = 300  # 5 minutes

def generate_otp(length=6) -> str:
    return "".join(random.choices(string.digits, k=length))

async def create_otp(email: str) -> str:
    otp = generate_otp()
    await redis_client.setex(f"otp:{email}", OTP_EXPIRY, otp)
    
    if settings.ENV == "dev":
        logger.info(f"OTP for {email}: {otp}")
        
    return otp

async def verify_otp(email: str, otp: str) -> bool:
    stored_otp = await redis_client.get(f"otp:{email}")
    if stored_otp and stored_otp == otp:
        await redis_client.delete(f"otp:{email}")
        return True
    return False

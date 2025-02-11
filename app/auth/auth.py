from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
    
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token - this is a sync function"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 24 hours
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify a JWT token - this is an async function since it's used in FastAPI endpoints"""
    try:
        # Log safely - only log that we received a token, not the token itself
        logger.debug("Verifying access token")
        
        # Verify token with minimal validation - just check signature and expiry
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={
                "verify_aud": False,  # Don't verify audience claim
                "verify_iss": False,  # Don't verify issuer claim
                "require_exp": True,  # But do require expiration
            }
        )
        # Log safely - only log non-sensitive parts of payload
        logger.debug(f"Token verified for user: {payload.get('sub', 'unknown')}")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError as e:
        logger.error("JWT validation error")  # Don't log the specific error
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error("Unexpected error during token verification")  # Don't log the specific error
        raise HTTPException(status_code=401, detail="Token verification failed")

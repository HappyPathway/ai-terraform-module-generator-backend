from enum import Enum
from fastapi import Depends, HTTPException
from typing import List
from ..auth import verify_token

class Permission(Enum):
    READ_MODULE = "read:module"
    WRITE_MODULE = "write:module"
    DELETE_MODULE = "delete:module"
    UPLOAD_MODULE = "upload:module"
    GENERATE_MODULE = "generate:module"

def check_permissions(required_permissions: List[Permission]):
    async def permission_checker(token: dict = Depends(verify_token)):
        user_permissions = token.get("permissions", [])
        for permission in required_permissions:
            if permission.value not in user_permissions:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token
    return permission_checker
from enum import Enum
from typing import List, Set
from pydantic import BaseModel

class Role(str, Enum):
    ADMIN = "admin"
    PUBLISHER = "publisher"
    READER = "reader"

class Permission(str, Enum):
    READ_MODULE = "read:module"
    UPLOAD_MODULE = "upload:module"
    DELETE_MODULE = "delete:module"
    MANAGE_USERS = "manage:users"
    GENERATE_MODULE = "generate:module"

ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.READ_MODULE,
        Permission.UPLOAD_MODULE,
        Permission.DELETE_MODULE,
        Permission.MANAGE_USERS,
        Permission.GENERATE_MODULE
    },
    Role.PUBLISHER: {
        Permission.READ_MODULE,
        Permission.UPLOAD_MODULE,
        Permission.GENERATE_MODULE
    },
    Role.READER: {
        Permission.READ_MODULE
    }
}

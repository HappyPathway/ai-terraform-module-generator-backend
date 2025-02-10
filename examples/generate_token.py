#!/usr/bin/env python3
from app.auth.auth import create_access_token
import asyncio

def generate_token():
    token_data = {
        "sub": "test-user",
        "permissions": [
            "read:module",
            "write:module",
            "upload:module",
            "generate:module"
        ]
    }
    return asyncio.run(create_access_token(token_data))

if __name__ == "__main__":
    token = generate_token()
    print(f"Generated token: {token}")
#!/usr/bin/env python3
import os
from app.auth.auth import create_access_token

def generate_token():
    if not os.environ.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
        
    token_data = {
        "sub": "test-user",
        "permissions": [
            "read:module",
            "write:module",
            "upload:module",
            "generate:module"
        ]
    }
    return create_access_token(token_data)

if __name__ == "__main__":
    token = generate_token()
    print(f"Generated token: {token}")
    print("\nMake sure to set this token in TERRAFORM_MODULE_TOKEN environment variable")
    print("Example: export TERRAFORM_MODULE_TOKEN='<token>'")
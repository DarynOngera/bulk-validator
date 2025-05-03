import os
from fastapi import Header, HTTPException, status, Depends
from dotenv import load_dotenv

load_dotenv()

# Example: comma-separated API keys for each role in .env
# API_KEYS_ADMIN=key1,key2
# API_KEYS_AUDITOR=aud1,aud2
# API_KEYS_USER=user1,user2

def get_role_from_api_key(api_key: str):
    admin_keys = os.getenv("API_KEYS_ADMIN", "").split(",")
    auditor_keys = os.getenv("API_KEYS_AUDITOR", "").split(",")
    user_keys = os.getenv("API_KEYS_USER", "").split(",")
    if api_key in admin_keys:
        return "admin"
    if api_key in auditor_keys:
        return "auditor"
    if api_key in user_keys:
        return "user"
    return None

def require_role(*roles):
    def dependency(api_key: str = Header(..., alias="x-api-key")):
        role = get_role_from_api_key(api_key)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {roles}, got: {role or 'none'}"
            )
        return role
    return dependency

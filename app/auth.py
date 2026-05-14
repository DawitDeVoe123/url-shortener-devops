from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
REALM = os.getenv("KEYCLOAK_REALM", "myrealm")

def get_public_key():
    """Get Keycloak public key for token validation"""
    try:
        response = requests.get(f"{KEYCLOAK_URL}/realms/{REALM}")
        if response.status_code == 200:
            return response.json().get("public_key")
    except Exception as e:
        print(f"Error getting public key: {e}")
    return None

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token with Keycloak"""
    token = credentials.credentials
    
    # Validate token with Keycloak's introspection endpoint
    try:
        # Call Keycloak to validate the token
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token/introspect",
            data={
                "token": token,
                "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "url-shortener"),
                "client_secret": os.getenv("KEYCLOAK_CLIENT_SECRET", "")
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("active"):
                # Token is valid, return user info
                return {
                    "sub": result.get("sub"),
                    "preferred_username": result.get("username"),
                    "email": result.get("email")
                }
        
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    except Exception as e:
        print(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
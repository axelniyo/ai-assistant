import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from functools import lru_cache
from jwt import PyJWKClient

app = FastAPI(
    title="Hello Copilot API (Secure)",
    description="A multi-tenant Entra ID protected API",
    version="1.0.0"
)

CLIENT_ID = os.getenv("CLIENT_ID")  # set this in Render env vars
JWKS_URL = "https://login.microsoftonline.com/common/discovery/v2.0/keys"

security = HTTPBearer()

# Use PyJWT 2.x PyJWKClient to fetch keys
@lru_cache
def get_jwk_client():
    return PyJWKClient(JWKS_URL)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    jwk_client = get_jwk_client()
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

@app.get("/")
def root():
    return {"message": "API is running. Try /hello or /secure-hello"}

@app.get("/hello")
def hello(name: str = "world"):
    return {"message": f"Hello, {name}"}

@app.get("/secure-hello")
def secure_hello(user=Depends(verify_token)):
    return {
        "message": f"Hello, {user.get('preferred_username', 'unknown user')}",
        "tenant": user.get("tid"),
        "audience": user.get("aud")
    }

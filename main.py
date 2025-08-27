import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from functools import lru_cache

app = FastAPI(
    title="Hello Copilot API (Secure)",
    description="A multi-tenant Entra ID protected API",
    version="1.0.0"
)

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

security = HTTPBearer()

@lru_cache
def get_jwks():
    resp = httpx.get(JWKS_URL)
    resp.raise_for_status()
    return resp.json()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == unverified_header["kid"])
        public_key = RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=f"api://{CLIENT_ID}",
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

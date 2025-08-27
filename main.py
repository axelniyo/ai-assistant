import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from functools import lru_cache

# ----------------------
# FastAPI App
# ----------------------
app = FastAPI(
    title="Hello Copilot API (Secure)",
    description="A multi-tenant Entra ID protected API",
    version="1.0.0"
)

# ----------------------
# Environment Variables
# ----------------------
CLIENT_ID = os.getenv("CLIENT_ID")  # e.g., "013d3676-c2a6-4c36-9c1b-5f37cad2b0f6"
TENANT_ID = os.getenv("TENANT_ID")  # e.g., "93650869-6c5c-4fbd-9cee-535fc31acdf9"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # e.g., "2iR8Q~VUucv_OyEE47EwZmtjZ1NL9ebtHU48sbvU"
JWKS_URL = "https://login.microsoftonline.com/common/discovery/v2.0/keys"

security = HTTPBearer()

# ----------------------
# JWT Verification
# ----------------------
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
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=f"api://{CLIENT_ID}")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

# ----------------------
# Basic Endpoints
# ----------------------
@app.get("/")
def root():
    return {"message": "API is running. Try /hello, /secure-hello, or /copilot-query"}

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

# ----------------------
# Microsoft Copilot Query Endpoint
# ----------------------
async def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "scope": f"api://{CLIENT_ID}/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

@app.post("/copilot-query")
async def copilot_query(prompt: str, user=Depends(verify_token)):
    access_token = await get_access_token()
    
    # Replace this URL with the correct Copilot Graph API endpoint
    copilot_endpoint = "https://graph.microsoft.com/beta/copilot/query"
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {"prompt": prompt}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(copilot_endpoint, json=payload, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

from fastapi import FastAPI
from pydantic import BaseModel  # Import BaseModel

# Create a model for the POST request data
class NameRequest(BaseModel):
    name: str

app = FastAPI(
    title="Hello Copilot API",
    description="A simple API to greet users",
    version="1.0.0"
)

# Your existing GET endpoint (good for testing)
@app.get("/hello")
def say_hello_get(name: str = "world"):
    return {"message": f"Hello, {name}"}

# NEW: Add this POST endpoint for Copilot
@app.post("/hello")
def say_hello_post(request: NameRequest):
    return {"message": f"Hello, {request.name}! This is your Copilot agent speaking."}

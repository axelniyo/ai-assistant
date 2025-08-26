from fastapi import FastAPI

app = FastAPI(
    title="Hello Copilot API",
    description="A simple API to greet users",
    version="1.0.0"
)

@app.get("/hello")
def say_hello(name: str = "world"):
    return {"message": f"Hello, {name}"}

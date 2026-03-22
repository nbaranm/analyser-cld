"""Application entrypoint."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api import router

app = FastAPI(title="GDA Game Analyzer", version="2.0.0")

@app.middleware("http")
async def add_cors(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse({}, status_code=200)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

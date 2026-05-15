import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from agent_service.app.logger import logger

app = FastAPI(title="Asset Analytics Agent Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "%s %s → %s  (%.0fms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}

from agent_service.app.agent_router import router as agent_router
app.include_router(agent_router)

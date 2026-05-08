from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Asset Analytics Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.activities.search import router as search_router
app.include_router(search_router)

from backend.app.activities.asset_detail import router as asset_router
app.include_router(asset_router)

from backend.app.activities.price_history import router as price_history_router
app.include_router(price_history_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

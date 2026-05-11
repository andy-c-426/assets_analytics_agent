import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.models.schemas import AnalysisRequest

router = APIRouter()

AGENT_SERVICE_URL = "http://localhost:8001"


@router.post("/api/analyze/{symbol}")
async def analyze_endpoint(symbol: str, body: AnalysisRequest):
    """Proxy the analyze request to the agent service, streaming SSE back."""
    client = httpx.AsyncClient(timeout=120.0)

    async def stream():
        try:
            async with client.stream(
                "POST",
                f"{AGENT_SERVICE_URL}/analyze/{symbol}",
                json={
                    "provider": body.provider,
                    "model": body.model,
                    "api_key": body.api_key,
                    "base_url": body.base_url,
                    "finnhub_api_key": body.finnhub_api_key,
                    "language": body.language,
                    "prefetched_data": body.prefetched_data,
                },
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
        finally:
            await client.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

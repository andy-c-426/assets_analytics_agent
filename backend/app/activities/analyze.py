from fastapi import APIRouter
from backend.app.models.schemas import AnalysisRequest, AnalysisResponse
from backend.app.proxy.yfinance import fetch_asset
from backend.app.proxy.llm import build_context, analyze as analyze_asset

router = APIRouter()


@router.post("/api/analyze/{symbol}", response_model=AnalysisResponse)
def analyze_endpoint(symbol: str, body: AnalysisRequest):
    asset = fetch_asset(symbol)
    context = build_context(asset)
    analysis_text = analyze_asset(
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
        context=context,
        base_url=body.base_url,
    )
    return AnalysisResponse(
        symbol=symbol,
        analysis=analysis_text,
        model_used=body.model,
        context_sent={
            "data_points": len(context.split("\n")),
            "news_count": len(asset.news),
        },
    )

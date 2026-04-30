import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.rag import search_relevant_info
from app.vision import analyze_image_with_gpt4o

logger = logging.getLogger(__name__)

app = FastAPI(title="First Aid Vision RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _format_analysis(summary: str, injury_type: str, urgency: str) -> str:
    pieces = [piece for piece in [injury_type, summary] if piece]
    analysis_text = " - ".join(pieces) if pieces else "상처 상태를 분석하지 못했습니다."
    if urgency:
        analysis_text = f"{analysis_text} (긴급도: {urgency})"
    return analysis_text


@app.get("/")
async def health_check():
    return {
        "status": "online",
        "api_key_loaded": bool(settings.OPENAI_API_KEY),
        "vision_model": settings.VISION_MODEL,
    }


@app.post("/analyze")
async def analyze_scene(file: UploadFile = File(...)):
    image_bytes = await file.read()
    if not image_bytes:
        return {
            "analysis": "분석 실패",
            "suggestion": "업로드된 이미지가 비어 있습니다. 다시 촬영해주세요.",
        }

    try:
        vision_result = await analyze_image_with_gpt4o(image_bytes)
    except Exception as exc:
        logger.exception("Vision analysis failed")
        return {
            "analysis": "분석 실패",
            "suggestion": f"이미지 분석 중 오류가 발생했습니다: {exc}",
        }

    analysis_text = _format_analysis(
        vision_result.summary,
        vision_result.injury_type,
        vision_result.urgency,
    )
    search_query = " ".join(vision_result.search_keywords).strip() or vision_result.summary

    try:
        manual_context = search_relevant_info(search_query)
    except Exception as exc:
        logger.exception("RAG lookup failed")
        return {
            "analysis": analysis_text,
            "suggestion": (
                f"즉시 조치 포인트: {vision_result.first_aid_focus}\n\n"
                f"매뉴얼 검색 중 오류가 발생했습니다: {exc}"
            ),
        }

    return {
        "analysis": analysis_text,
        "suggestion": (
            f"즉시 조치 포인트: {vision_result.first_aid_focus}\n\n"
            f"매뉴얼 기반 가이드:\n{manual_context}"
        ),
    }

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title='First Aid Vision RAG API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {"status": "online", "api_key_loaded": bool(settings.OPENAI_API_KEY)}

@app.post("/analyze")
async def analyze_scene(file: UploadFile = File(...)):
    """
    프론트엔드에서 보낸 이미지를 받는 엔드포인트입니다.
    """
    # 1. 이미지 수신 확인
    # 2. Vision API 호출 로직 (진행 예정)
    # 3. RAG 검색 로직 (진행 예정)
    return {
        "analysis": "이미지가 성공적으로 수신되었습니다.",
        "suggestion": "조금만 기다려주시면 분석 결과를 보내드립니다."
    }
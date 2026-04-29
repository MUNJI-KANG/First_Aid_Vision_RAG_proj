import base64
import httpx
from app.config import settings  # settings 인스턴스를 가져옵니다

async def analyze_image_with_gpt4o(image_bytes: bytes):
    """
    GPT-4o Vision API를 사용하여 상처 부위를 분석합니다.
    """
    # 1. 이미지를 Base64 문자열로 인코딩 (OpenAI 규격)
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
    }

    # 2. 페이로드 작성 (응급처치 전문가 페르소나 부여)
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "당신은 응급처치 전문가입니다. 사진 속의 상처나 응급 상황을 분석하세요. "
                            "결과는 다음 형식을 엄격히 지켜서 한국어로 답변하세요.\n"
                            "상황 판단: [어떤 종류의 상처인지, 상태가 어떤지 요약]\n"
                            "긴급도: [낮음/중간/높음]"
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    # 3. 비동기 HTTP 클라이언트로 호출 (서버 멈춤 방지)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
    # 4. 결과값 처리
    if response.status_code != 200:
        return f"Error: API 호출 실패 (Status: {response.status_code})"
        
    result = response.json()
    return result['choices'][0]['message']['content']
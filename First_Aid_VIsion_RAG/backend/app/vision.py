import base64
import json

import cv2
import numpy as np
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, OpenAIError

from app.config import settings
from app.schema import VisionAnalysis

MAX_IMAGE_DIMENSION = 1024
JPEG_QUALITY = 70

client_kwargs = {"api_key": settings.OPENAI_API_KEY}
if settings.OPENAI_BASE_URL:
    client_kwargs["base_url"] = settings.OPENAI_BASE_URL

client = AsyncOpenAI(**client_kwargs)


def _prepare_image_for_vision(image_bytes: bytes) -> bytes:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a valid image.")

    height, width = image.shape[:2]
    longest_edge = max(height, width)
    if longest_edge > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / float(longest_edge)
        resized_width = max(1, int(width * scale))
        resized_height = max(1, int(height * scale))
        image = cv2.resize(
            image,
            (resized_width, resized_height),
            interpolation=cv2.INTER_AREA,
        )

    success, encoded_image = cv2.imencode(
        ".jpg",
        image,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
    )
    if not success:
        raise RuntimeError("Failed to encode image for vision request.")

    return encoded_image.tobytes()


def _normalize_keywords(raw_keywords: object) -> list[str]:
    if isinstance(raw_keywords, list):
        return [str(keyword).strip() for keyword in raw_keywords if str(keyword).strip()]
    if isinstance(raw_keywords, str):
        return [keyword.strip() for keyword in raw_keywords.split(",") if keyword.strip()]
    return []


async def analyze_image_with_gpt4o(image_bytes: bytes) -> VisionAnalysis:
    if not image_bytes:
        raise ValueError("Uploaded image is empty.")

    optimized_image = _prepare_image_for_vision(image_bytes)
    base64_image = base64.b64encode(optimized_image).decode("utf-8")

    try:
        response = await client.chat.completions.create(
            model=settings.VISION_MODEL,
            response_format={"type": "json_object"},
            max_tokens=400,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a first-aid training assistant. Analyze only visible injuries. "
                        "Do not diagnose hidden conditions. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze the wound in this image and respond in Korean as JSON with "
                                "the keys: summary, injury_type, urgency, first_aid_focus, search_keywords. "
                                "search_keywords must be an array of short Korean keywords for manual lookup."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low",
                            },
                        },
                    ],
                },
            ],
        )
    except APITimeoutError as exc:
        raise RuntimeError("OpenAI vision request timed out.") from exc
    except APIConnectionError as exc:
        raise RuntimeError("OpenAI vision request could not reach the API.") from exc
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI vision request failed: {exc}") from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError) as exc:
        raise RuntimeError("OpenAI vision response format was unexpected.") from exc

    if not content:
        raise RuntimeError("OpenAI vision response was empty.")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI vision response was not valid JSON: {content}") from exc

    analysis = VisionAnalysis(
        summary=str(parsed.get("summary", "")).strip(),
        injury_type=str(parsed.get("injury_type", "")).strip(),
        urgency=str(parsed.get("urgency", "")).strip(),
        first_aid_focus=str(parsed.get("first_aid_focus", "")).strip(),
        search_keywords=_normalize_keywords(parsed.get("search_keywords")),
    )

    if not analysis.summary:
        raise RuntimeError("Vision analysis did not include a summary.")

    if not analysis.search_keywords:
        fallback_keywords = [analysis.injury_type, analysis.urgency, analysis.summary]
        analysis.search_keywords = [keyword for keyword in fallback_keywords if keyword]

    return analysis

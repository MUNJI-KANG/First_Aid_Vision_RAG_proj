from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # .env 파일에 작성하신 변수명과 정확히 일치해야 합니다.
    OPENAI_API_KEY: str

    # backend/ 폴더에 있는 .env 파일을 읽어오도록 설정
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()
def get_settings():
    """설정 객체를 생성하고 캐싱합니다."""
    return Settings()

# !!! 중요: 이 줄이 있어야 main.py에서 'from app.config import settings'가 가능합니다.
settings = get_settings()
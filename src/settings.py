from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    NOTION_API_KEY: str
    NOTION_DATABASE_ID: list[str]

    STATUS_TO_INCLUDE: list[str] = ["Signed", "Follow up"]

    CACHE_TIME: int = 10

    MAP_CENTER: list[float] = [24.7136, 46.6753]
    MAP_ZOOM: int = 11
    MAP_NAME: str = 'My Map'

    class Config:
        env_file = ".env"



@lru_cache
def get_settings():
    return Settings()  # type: ignore


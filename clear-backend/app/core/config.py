# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CLEAR Backend"
    API_V1_STR: str = "/api/v1"

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    SEGMENTS_JSON_PATH: str = "./data/segments.json"
    SDKG_INDEX_JSON_PATH: str = "./data/sdkg_index.json"
    SDKG_NODES_DIR: str = "./data/nodes"
    SUBGRAPH_DIR: str = "./data/subgraph"

    class Config:
        env_file = ".env"


settings = Settings()

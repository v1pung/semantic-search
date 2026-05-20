from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # PostgreSQL
    POSTGRES_USER: str = Field(description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(description="PostgreSQL password")
    POSTGRES_DB: str = Field(description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(description="PostgreSQL hostname")
    POSTGRES_PORT: str = Field(default="5432", description="PostgreSQL port")

    # Redis
    REDIS_HOST: str = Field(description="Redis hostname")
    REDIS_PORT: str = Field(default="6379", description="Redis port")

    # Qdrant
    QDRANT_HOST: str = Field(description="Qdrant service hostname")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant REST API port")
    QDRANT_COLLECTION: str = Field(default="qa_pairs")

    # Application
    CSV_PATH: str = Field(default="data/qa_pairs.csv")
    EMBEDDING_MODEL: str = Field(default="paraphrase-multilingual-MiniLM-L12-v2")
    SEARCH_TOP_K: int = Field(default=5, ge=1, le=20)

    # Computed connection URLs

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_BROKER_DB: int = Field(default=0, description="Redis DB index for Celery broker")
    REDIS_BACKEND_DB: int = Field(default=1, description="Redis DB index for Celery result backend")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_BROKER_DB}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_BACKEND_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_BACKEND_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

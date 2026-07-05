from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    qdrant_url: str
    ollama_url: str
    ollama_model: str


# единый объект настроек, импортируется по всему приложению
settings = Settings()
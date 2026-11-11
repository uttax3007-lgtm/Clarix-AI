from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "clarix"
    firebase_credentials_path: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-001"
    storage_dir: str = "./storage"
    max_upload_mb: int = 15
    cors_origins: str = "http://localhost:3000"
    whisper_model: str = "small"

settings = Settings()

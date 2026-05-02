from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str 
    MINIO_BUCKET_NAME: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
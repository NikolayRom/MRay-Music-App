from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MINIO_URL: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str 
    MINIO_BUCKET_NAME: str

    POSTGRES_URL: str

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')

settings = Settings()
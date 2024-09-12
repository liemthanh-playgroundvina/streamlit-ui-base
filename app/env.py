from pydantic import BaseSettings
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Settings(BaseSettings):
    # Backend URLs
    AUTHORIZATION: str
    CHAT_URL: str
    CHAT_VISION_URL: str
    CHAT_DOC_EMBED_URL: str
    QUEUE_STATUS_URL: str
    CHAT_DOC_LC_URL: str
    CHAT_DOC_RAG_URL: str

    GPTS_FILE_PATH: str
    LLMS_FILE_PATH: str

    # S3 Configurations
    AWS_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_ACL: str

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")

settings = Settings()

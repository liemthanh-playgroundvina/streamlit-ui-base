import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Settings():
    # Backend URLs
    AUTHORIZATION = os.getenv("AUTHORIZATION")
    CHAT_URL = os.getenv("CHAT_URL")
    CHAT_VISION_URL = os.getenv("CHAT_VISION_URL")
    CHAT_DOC_EMBED_URL = os.getenv("CHAT_DOC_EMBED_URL")
    CHAT_DOC_LC_URL = os.getenv("CHAT_DOC_LC_URL")
    CHAT_DOC_RAG_URL = os.getenv("CHAT_DOC_RAG_URL")

    GPTS_FILE_PATH = os.getenv("GPTS_FILE_PATH")
    LLMS_FILE_PATH = os.getenv("LLMS_FILE_PATH")

    # S3 Configurations
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_ACL = os.getenv("AWS_ACL")

settings = Settings()

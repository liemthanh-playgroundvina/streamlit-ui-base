import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
load_dotenv(".env")


class Settings():
    AUTHORIZATION = os.getenv("AUTHORIZATION")
    AI_CENTER_BE_URL = os.getenv("AI_CENTER_BE_URL")
    # S3
    AWS_REGION = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
    AWS_ACL = os.getenv("AWS_ACL")


settings = Settings()

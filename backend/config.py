import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    AWS_PROFILE = os.getenv("AWS_PROFILE", "postagens-diarias")
    AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")

    AWS_S3_BUCKET = os.getenv(
        "AWS_S3_BUCKET",
        "postagens-diarias"
    )

    AWS_S3_PREFIX = os.getenv(
        "AWS_S3_PREFIX",
        "banco-fotos/"
    )

    INSTAGRAM_API_VERSION = os.getenv(
        "INSTAGRAM_API_VERSION",
        "v25.0"
    )

    INSTAGRAM_USER_ID = os.getenv(
        "INSTAGRAM_USER_ID"
    )

    INSTAGRAM_ACCESS_TOKEN = os.getenv(
        "INSTAGRAM_ACCESS_TOKEN"
    )

    INSTAGRAM_GRAPH_URL = (
        f"https://graph.instagram.com/"
        f"{INSTAGRAM_API_VERSION}"
    )
    
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_TIMEZONE = os.getenv(
        "APP_TIMEZONE",
        "America/Sao_Paulo"
    )
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import ROOT_DIR


# ------------------------------------ Settings ------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / '.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    BOT_TOKEN: str


settings = Settings()

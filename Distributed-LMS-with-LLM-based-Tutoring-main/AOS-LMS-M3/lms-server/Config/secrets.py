from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    AES_SECRET: str
    NODE_ID : str
    class Config:
        env_file = ".env"

settings = Settings()
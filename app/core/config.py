from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()

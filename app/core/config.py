from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_api_base: str
    model_name: str

    class Config:
        env_file = ".env"
        # 允许额外字段，防止 .env 中有其他无关变量导致报错
        extra = "ignore" 

settings = Settings()
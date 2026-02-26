from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # OpenAI 配置
    openai_api_key: str
    openai_api_base: str
    model_name: str

    # 蒸馏服务配置
    default_webhook_url: str = "http://localhost:3000/api/webhooks/ai-distilled"
    task_timeout: int = 600  # 10分钟超时
    webhook_timeout: int = 30  # Webhook 回调超时时间（秒）

    # 文本切片配置
    chunk_size: int = 10000
    chunk_overlap: int = 2000

    # 蒸馏配置
    max_refine_iterations: int = 50  # 最大 Refine 迭代次数
    summary_target_ratio: float = 0.3  # 目标摘要比例（原文的30%）

    # 速率限制配置
    api_request_delay: float = 1.0  # API 请求间延迟（秒）
    max_retries: int = 3  # 最大重试次数
    initial_retry_delay: float = 2.0  # 初始重试延迟（秒）

    class Config:
        env_file = ".env"
        # 允许额外字段，防止 .env 中有其他无关变量导致报错
        extra = "ignore"

settings = Settings()
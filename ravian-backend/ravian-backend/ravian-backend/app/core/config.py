"""
Application configuration settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application settings
    app_name: str = "Ravian Backend API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Security settings
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY", default="your-secret-key-here-change-in-production")
    jwt_algorithm: str = Field(env="JWT_ALGORITHM", default="HS256")
    jwt_access_token_expire_minutes: int = Field(env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=30)  # 30 min per TA integration spec
    jwt_refresh_token_expire_days: int = Field(env="JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7)
    
    # Database settings
    db_host: str = Field(env="DB_HOST", default="localhost")
    db_port: int = Field(env="DB_PORT", default=5432)
    db_user: str = Field(env="DB_USER", default="postgres")
    db_password: str = Field(env="DB_PASSWORD", default="password")
    db_name: str = Field(env="DB_NAME", default="ravian_db")
    db_pool_size: int = Field(env="DB_POOL_SIZE", default=20)
    db_max_overflow: int = Field(env="DB_MAX_OVERFLOW", default=30)
    db_pool_recycle: int = Field(env="DB_POOL_RECYCLE", default=3600)
    db_echo: bool = Field(env="DB_ECHO", default=False)
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Redis settings
    redis_host: str = Field(env="REDIS_HOST", default="localhost")
    redis_port: int = Field(env="REDIS_PORT", default=6379)
    redis_db: int = Field(env="REDIS_DB", default=0)
    redis_password: Optional[str] = Field(env="REDIS_PASSWORD", default=None)
    redis_ssl: bool = Field(env="REDIS_SSL", default=False)
    redis_max_connections: int = Field(env="REDIS_MAX_CONNECTIONS", default=50)
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Rate limiting settings
    rate_limiting_enabled: bool = Field(env="RATE_LIMITING_ENABLED", default=True)
    rate_limiting_algorithm: str = Field(env="RATE_LIMITING_ALGORITHM", default="sliding_window")
    rate_limiting_fail_open: bool = Field(env="RATE_LIMITING_FAIL_OPEN", default=True)
    rate_limiting_log_violations: bool = Field(env="RATE_LIMITING_LOG_VIOLATIONS", default=True)
    
    # Rate limits per tier (requests per minute)
    rate_limit_starter_per_minute: int = Field(env="RATE_LIMIT_STARTER_PER_MINUTE", default=100)
    rate_limit_starter_per_hour: int = Field(env="RATE_LIMIT_STARTER_PER_HOUR", default=1000)
    rate_limit_starter_per_day: int = Field(env="RATE_LIMIT_STARTER_PER_DAY", default=10000)
    
    rate_limit_growth_per_minute: int = Field(env="RATE_LIMIT_GROWTH_PER_MINUTE", default=500)
    rate_limit_growth_per_hour: int = Field(env="RATE_LIMIT_GROWTH_PER_HOUR", default=10000)
    rate_limit_growth_per_day: int = Field(env="RATE_LIMIT_GROWTH_PER_DAY", default=100000)
    
    rate_limit_enterprise_per_minute: int = Field(env="RATE_LIMIT_ENTERPRISE_PER_MINUTE", default=2000)
    rate_limit_enterprise_per_hour: int = Field(env="RATE_LIMIT_ENTERPRISE_PER_HOUR", default=50000)
    rate_limit_enterprise_per_day: int = Field(env="RATE_LIMIT_ENTERPRISE_PER_DAY", default=1000000)
    
    rate_limit_admin_per_minute: int = Field(env="RATE_LIMIT_ADMIN_PER_MINUTE", default=10000)
    rate_limit_admin_per_hour: int = Field(env="RATE_LIMIT_ADMIN_PER_HOUR", default=100000)
    rate_limit_admin_per_day: int = Field(env="RATE_LIMIT_ADMIN_PER_DAY", default=10000000)
    
    # Endpoint multipliers
    rate_limit_chatbot_multiplier: float = Field(env="RATE_LIMIT_CHATBOT_MULTIPLIER", default=1.0)
    rate_limit_leads_multiplier: float = Field(env="RATE_LIMIT_LEADS_MULTIPLIER", default=0.5)
    rate_limit_calls_multiplier: float = Field(env="RATE_LIMIT_CALLS_MULTIPLIER", default=0.3)
    rate_limit_demos_multiplier: float = Field(env="RATE_LIMIT_DEMOS_MULTIPLIER", default=0.2)
    rate_limit_analytics_multiplier: float = Field(env="RATE_LIMIT_ANALYTICS_MULTIPLIER", default=0.1)
    rate_limit_teaching_multiplier: float = Field(env="RATE_LIMIT_TEACHING_MULTIPLIER", default=0.5)
    rate_limit_context_multiplier: float = Field(env="RATE_LIMIT_CONTEXT_MULTIPLIER", default=1.0)
    
    # Exemptions
    rate_limit_exempt_ips: str = Field(env="RATE_LIMIT_EXEMPT_IPS", default="127.0.0.1,::1")
    rate_limit_exempt_user_agents: str = Field(env="RATE_LIMIT_EXEMPT_USER_AGENTS", default="HealthCheck")
    rate_limit_exempt_paths: str = Field(env="RATE_LIMIT_EXEMPT_PATHS", default="/health,/docs,/redoc,/openapi.json")
    
    # Celery settings
    celery_broker_url: str = Field(env="CELERY_BROKER_URL", default="redis://localhost:6379/1")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
    celery_include: list = ["app.tasks"]
    
    # CORS settings
    cors_origins: str = Field(env="CORS_ORIGINS", default="http://localhost:3000,http://localhost:8080")
    cors_allow_credentials: bool = Field(env="CORS_ALLOW_CREDENTIALS", default=True)
    cors_allow_methods: str = Field(env="CORS_ALLOW_METHODS", default="GET,POST,PUT,DELETE,OPTIONS")
    cors_allow_headers: str = Field(env="CORS_ALLOW_HEADERS", default="*")
    
    # API settings
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # File upload settings
    max_upload_size: int = Field(env="MAX_UPLOAD_SIZE", default=10485760)  # 10MB
    upload_dir: str = Field(env="UPLOAD_DIR", default="uploads")
    
    # External service settings
    openai_api_key: Optional[str] = Field(env="OPENAI_API_KEY", default=None)
    twilio_account_sid: Optional[str] = Field(env="TWILIO_ACCOUNT_SID", default=None)
    twilio_auth_token: Optional[str] = Field(env="TWILIO_AUTH_TOKEN", default=None)
    vapi_api_key: Optional[str] = Field(env="VAPI_API_KEY", default=None)
    vapi_assistant_id: Optional[str] = Field(env="VAPI_ASSISTANT_ID", default=None)
    vapi_phone_number_id: Optional[str] = Field(env="VAPI_PHONE_NUMBER_ID", default=None)

    # Teaching Assistant
    chroma_db_path: str = Field(env="CHROMA_DB_PATH", default="./chroma_db")
    whisper_model: str = Field(env="WHISPER_MODEL", default="base")
    ta_embedding_model: str = Field(env="TA_EMBEDDING_MODEL", default="text-embedding-3-small")
    ta_llm_model: str = Field(env="TA_LLM_MODEL", default="gpt-4o-mini")
    ta_tts_model: str = Field(env="TA_TTS_MODEL", default="tts-1")
    ta_tts_voice: str = Field(env="TA_TTS_VOICE", default="nova")
    audio_storage_path: str = Field(env="AUDIO_STORAGE_PATH", default="./storage/audio")
    documents_storage_path: str = Field(env="DOCUMENTS_STORAGE_PATH", default="./storage/documents")
    ta_chunk_size: int = Field(env="TA_CHUNK_SIZE", default=800)
    ta_chunk_overlap: int = Field(env="TA_CHUNK_OVERLAP", default=100)

    # Chatbot settings
    chatbot_api_key: Optional[str] = Field(env="CHATBOT_API_KEY", default=None)
    chatbot_model: str = Field(env="CHATBOT_MODEL", default="gpt-4")
    chatbot_temperature: float = Field(env="CHATBOT_TEMPERATURE", default=0.7)
    chatbot_enabled: bool = Field(env="CHATBOT_ENABLED", default=True)

    # Widget settings
    chatbot_widget_enabled: bool = Field(env="CHATBOT_WIDGET_ENABLED", default=True)
    chatbot_widget_url: str = Field(env="CHATBOT_WIDGET_URL", default="http://localhost:3000/chatbot-widget.js")

    # Google Calendar integration
    google_calendar_credentials_file: Optional[str] = Field(env="GOOGLE_CALENDAR_CREDENTIALS_FILE", default=None)
    google_calendar_id: str = Field(env="GOOGLE_CALENDAR_ID", default="primary")

    # Intent recognition settings (enable when OPENAI_API_KEY or CHATBOT_API_KEY is set)
    intent_recognition_enabled: bool = Field(env="INTENT_RECOGNITION_ENABLED", default=True)
    intent_recognition_model: str = Field(env="INTENT_RECOGNITION_MODEL", default="gpt-3.5-turbo")
    intent_recognition_endpoint: str = Field(env="INTENT_RECOGNITION_ENDPOINT", default="")
    # Production intent classifier (COURSE_INQUIRY, FEE_QUERY, etc.)
    use_production_intent_classifier: bool = Field(env="USE_PRODUCTION_INTENT_CLASSIFIER", default=True)

    # Analytics settings
    analytics_enabled: bool = Field(env="ANALYTICS_ENABLED", default=True)
    analytics_batch_size: int = Field(env="ANALYTICS_BATCH_SIZE", default=100)
    analytics_retention_days: int = Field(env="ANALYTICS_RETENTION_DAYS", default=365)
    
    # Logging settings
    log_level: str = Field(env="LOG_LEVEL", default="INFO")

    # API Information
    api_title: str = Field(env="API_TITLE", default="Ravian Backend API")
    api_description: str = Field(env="API_DESCRIPTION", default="Backend API for Ravian Platform")
    api_version: str = Field(env="API_VERSION", default="1.0.0")

    # Server settings
    host: str = Field(env="HOST", default="0.0.0.0")
    port: int = Field(env="PORT", default=8000)
    workers: int = Field(env="WORKERS", default=1)

    # Security
    https_only: bool = Field(env="HTTPS_ONLY", default=False)
    allowed_hosts: str = Field(env="ALLOWED_HOSTS", default="*")

    # CORS additional settings
    cors_credentials: bool = Field(env="CORS_CREDENTIALS", default=True)
    cors_methods: str = Field(env="CORS_METHODS", default="GET,POST,PUT,DELETE,OPTIONS")
    cors_headers: str = Field(env="CORS_HEADERS", default="*")

    # Redis additional settings
    redis_pool_size: int = Field(env="REDIS_POOL_SIZE", default=50)
    redis_timeout: int = Field(env="REDIS_TIMEOUT", default=5)

    # Rate limiting
    rate_limit_enabled: bool = Field(env="RATE_LIMIT_ENABLED", default=True)
    rate_limit_fail_open: bool = Field(env="RATE_LIMIT_FAIL_OPEN", default=True)
    rate_limit_log_violations: bool = Field(env="RATE_LIMIT_LOG_VIOLATIONS", default=True)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars (e.g. TA_TTS_MODEL) not yet in code
        case_sensitive=False,
    )

# Global settings instance
settings = Settings()


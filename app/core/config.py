import os
from typing import Optional, List
from pydantic import validator, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "ContractCritic API"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 5000
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    allowed_hosts: str = Field(default="*", alias="ALLOWED_HOSTS")
    
    # Security settings
    secret_key: str = "asdf#FGSgvasgf$5$WGT"  # Should be overridden in production
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    
    # Supabase settings
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")
    
    # OpenRouter/OpenAI settings
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENAI_BASE_URL")
    site_title: str = Field(default="ContractCritic", alias="SITE_TITLE")
    
    # Vercel Blob Storage settings
    blob_read_write_token: Optional[str] = Field(default=None, alias="BLOB_READ_WRITE_TOKEN")
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {"pdf", "docx", "doc", "txt"}
    
    # Logging settings
    log_level: str = "WARNING"
    
    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError("SUPABASE_URL must be set")
        return v
    
    @validator("supabase_anon_key")
    def validate_supabase_anon_key(cls, v):
        if not v:
            raise ValueError("SUPABASE_ANON_KEY must be set")
        return v
    
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        """Parse ALLOWED_HOSTS from comma-separated string"""
        if isinstance(self.allowed_hosts, str):
            return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return self.allowed_hosts
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """Return OpenAI API key, preferring openai_api_key over openrouter_api_key"""
        return self.openai_api_key or self.openrouter_api_key
    
    @property
    def OPENAI_BASE_URL(self) -> str:
        """Return OpenAI base URL"""
        return self.openai_base_url or self.openrouter_base_url

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
settings = Settings()

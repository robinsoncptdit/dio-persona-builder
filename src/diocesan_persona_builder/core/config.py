"""Configuration module using Pydantic for type safety and validation."""

from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ONetCredentials(BaseModel):
    """O*NET API credentials model."""
    
    username: str = Field(..., description="O*NET API username")
    password: SecretStr = Field(..., description="O*NET API password")
    
    @property
    def auth_tuple(self) -> tuple[str, str]:
        """Return auth tuple for requests library."""
        return (self.username, self.password.get_secret_value())


class APIConfig(BaseModel):
    """API configuration settings."""
    
    base_url: str = Field(
        default="https://services.onetcenter.org/ws",
        description="O*NET Web Services base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    rate_limit_delay: float = Field(default=0.5, description="Delay between API calls")


class OutputConfig(BaseModel):
    """Output configuration settings."""
    
    output_dir: Path = Field(default=Path("output"), description="Output directory for personas")
    template_dir: Path = Field(default=Path("templates"), description="Template directory")
    file_pattern: str = Field(
        default="persona_{role_slug}.md",
        description="Output filename pattern"
    )
    
    @validator("output_dir", "template_dir")
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class CSVConfig(BaseModel):
    """CSV input configuration."""
    
    file_path: Path = Field(..., description="Path to diocesan roles CSV")
    required_columns: list[str] = Field(
        default=[
            "role_title",
            "setting",
            "onet_code", 
            "onet_title",
            "mapping_notes"
        ],
        description="Required CSV columns"
    )
    
    @validator("file_path")
    def validate_csv_exists(cls, v: Path) -> Path:
        """Validate CSV file exists."""
        if not v.exists():
            raise ValueError(f"CSV file not found: {v}")
        if v.suffix.lower() != ".csv":
            raise ValueError(f"File must be a CSV: {v}")
        return v


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # O*NET Credentials
    onet_username: str = Field(..., description="O*NET API username")
    onet_password: SecretStr = Field(..., description="O*NET API password")
    
    # Configurations
    api_config: APIConfig = Field(default_factory=APIConfig)
    output_config: OutputConfig = Field(default_factory=OutputConfig)
    
    # CSV path can be set via env or CLI
    csv_path: Optional[Path] = Field(None, description="Path to diocesan roles CSV")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(None, description="Log file path")
    
    # OpenAI API for technology filtering
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for technology filtering")
    
    @property
    def credentials(self) -> ONetCredentials:
        """Get O*NET credentials object."""
        return ONetCredentials(
            username=self.onet_username,
            password=self.onet_password
        )
    
    def get_csv_config(self, csv_path: Optional[Path] = None) -> CSVConfig:
        """Get CSV configuration with optional override."""
        path = csv_path or self.csv_path
        if not path:
            raise ValueError("CSV path must be provided")
        return CSVConfig(file_path=path)


def load_settings(**overrides: Any) -> Settings:
    """Load settings with optional overrides."""
    return Settings(**overrides)
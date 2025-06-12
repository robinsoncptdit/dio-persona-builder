"""Tests for configuration module."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from diocesan_persona_builder.core.config import (
    ONetCredentials,
    APIConfig,
    OutputConfig,
    CSVConfig,
    Settings
)


class TestONetCredentials:
    """Tests for ONetCredentials model."""
    
    def test_valid_credentials(self):
        """Test valid credentials creation."""
        creds = ONetCredentials(
            username="testuser",
            password="testpass"
        )
        assert creds.username == "testuser"
        assert creds.auth_tuple == ("testuser", "testpass")
    
    def test_empty_username(self):
        """Test validation with empty username."""
        with pytest.raises(ValidationError):
            ONetCredentials(username="", password="testpass")
    
    def test_empty_password(self):
        """Test validation with empty password."""
        with pytest.raises(ValidationError):
            ONetCredentials(username="testuser", password="")


class TestAPIConfig:
    """Tests for APIConfig model."""
    
    def test_default_config(self):
        """Test default API configuration."""
        config = APIConfig()
        assert config.base_url == "https://services.onetcenter.org/ws"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.rate_limit_delay == 0.5
    
    def test_custom_config(self):
        """Test custom API configuration."""
        config = APIConfig(
            base_url="https://example.com",
            timeout=60,
            max_retries=5
        )
        assert config.base_url == "https://example.com"
        assert config.timeout == 60
        assert config.max_retries == 5


class TestOutputConfig:
    """Tests for OutputConfig model."""
    
    def test_default_config(self, tmp_path):
        """Test default output configuration."""
        # Change to tmp directory to avoid creating real directories
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)
            
            config = OutputConfig()
            assert config.output_dir.name == "output"
            assert config.template_dir.name == "templates"
            assert config.file_pattern == "persona_{role_slug}.md"
            
            # Check directories were created
            assert config.output_dir.exists()
            assert config.template_dir.exists()
        finally:
            os.chdir(original_cwd)
    
    def test_custom_paths(self, tmp_path):
        """Test custom output paths."""
        output_dir = tmp_path / "custom_output"
        template_dir = tmp_path / "custom_templates"
        
        config = OutputConfig(
            output_dir=output_dir,
            template_dir=template_dir,
            file_pattern="custom_{role_slug}.md"
        )
        
        assert config.output_dir == output_dir
        assert config.template_dir == template_dir
        assert config.file_pattern == "custom_{role_slug}.md"
        
        # Check directories were created
        assert output_dir.exists()
        assert template_dir.exists()


class TestCSVConfig:
    """Tests for CSVConfig model."""
    
    def test_valid_csv_file(self, tmp_path):
        """Test valid CSV file configuration."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("role_title,setting,onet_code,onet_title,mapping_notes\n")
        
        config = CSVConfig(file_path=csv_file)
        assert config.file_path == csv_file
        assert len(config.required_columns) == 5
    
    def test_missing_csv_file(self, tmp_path):
        """Test validation with missing CSV file."""
        csv_file = tmp_path / "missing.csv"
        
        with pytest.raises(ValidationError):
            CSVConfig(file_path=csv_file)
    
    def test_non_csv_file(self, tmp_path):
        """Test validation with non-CSV file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test content")
        
        with pytest.raises(ValidationError):
            CSVConfig(file_path=txt_file)


class TestSettings:
    """Tests for Settings model."""
    
    def test_settings_creation(self):
        """Test settings creation with required fields."""
        settings = Settings(
            onet_username="testuser",
            onet_password="testpass"
        )
        
        assert settings.onet_username == "testuser"
        assert settings.credentials.username == "testuser"
        assert isinstance(settings.api_config, APIConfig)
        assert isinstance(settings.output_config, OutputConfig)
    
    def test_missing_credentials(self):
        """Test validation with missing credentials."""
        with pytest.raises(ValidationError):
            Settings()
    
    def test_csv_config_creation(self, tmp_path):
        """Test CSV config creation."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("role_title,setting,onet_code,onet_title,mapping_notes\n")
        
        settings = Settings(
            onet_username="testuser",
            onet_password="testpass",
            csv_path=csv_file
        )
        
        csv_config = settings.get_csv_config()
        assert csv_config.file_path == csv_file
    
    def test_csv_config_override(self, tmp_path):
        """Test CSV config with path override."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("role_title,setting,onet_code,onet_title,mapping_notes\n")
        
        settings = Settings(
            onet_username="testuser",
            onet_password="testpass"
        )
        
        csv_config = settings.get_csv_config(csv_file)
        assert csv_config.file_path == csv_file
    
    def test_csv_config_no_path(self):
        """Test CSV config with no path provided."""
        settings = Settings(
            onet_username="testuser",
            onet_password="testpass"
        )
        
        with pytest.raises(ValueError, match="CSV path must be provided"):
            settings.get_csv_config()
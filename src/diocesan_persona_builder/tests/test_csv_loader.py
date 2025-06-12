"""Tests for CSV loader module."""

import pytest
import pandas as pd
from pathlib import Path
from pydantic import ValidationError

from diocesan_persona_builder.core.csv_loader import DiocesanRole, CSVLoader
from diocesan_persona_builder.core.config import CSVConfig


class TestDiocesanRole:
    """Tests for DiocesanRole model."""
    
    def test_valid_role(self):
        """Test valid role creation."""
        role = DiocesanRole(
            role_title="Parish Secretary",
            setting="Parish",
            onet_code="43-6014.00",
            onet_title="Secretaries and Administrative Assistants",
            mapping_notes="Core administrative role"
        )
        
        assert role.role_title == "Parish Secretary"
        assert role.setting == "Parish"
        assert role.onet_code == "43-6014.00"
        assert role.onet_title == "Secretaries and Administrative Assistants"
        assert role.mapping_notes == "Core administrative role"
    
    def test_role_slug_generation(self):
        """Test role slug generation."""
        role = DiocesanRole(
            role_title="Youth Ministry Coordinator",
            setting="Parish Office",
            onet_code="21-1021.00",
            onet_title="Child, Family, and School Social Workers"
        )
        
        slug = role.role_slug
        assert slug == "youth_ministry_coordinator_parish_office"
        assert " " not in slug
        assert slug.islower()
    
    def test_role_slug_special_characters(self):
        """Test role slug with special characters."""
        role = DiocesanRole(
            role_title="Director of Faith Formation & Education",
            setting="K-12 School",
            onet_code="25-9031.00",
            onet_title="Instructional Coordinators"
        )
        
        slug = role.role_slug
        assert "&" not in slug
        assert "-" not in slug
        assert "_" in slug
    
    def test_invalid_onet_code(self):
        """Test validation with invalid O*NET code."""
        with pytest.raises(ValidationError):
            DiocesanRole(
                role_title="Test Role",
                setting="Test Setting",
                onet_code="invalid",
                onet_title="Test Title"
            )
    
    def test_empty_onet_code(self):
        """Test validation with empty O*NET code."""
        with pytest.raises(ValidationError):
            DiocesanRole(
                role_title="Test Role",
                setting="Test Setting",
                onet_code="",
                onet_title="Test Title"
            )
    
    def test_default_mapping_notes(self):
        """Test default empty mapping notes."""
        role = DiocesanRole(
            role_title="Test Role",
            setting="Test Setting",
            onet_code="43-6014.00",
            onet_title="Test Title"
        )
        
        assert role.mapping_notes == ""


class TestCSVLoader:
    """Tests for CSVLoader class."""
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return [
            {
                "role_title": "Parish Secretary",
                "setting": "Parish",
                "onet_code": "43-6014.00",
                "onet_title": "Secretaries and Administrative Assistants",
                "mapping_notes": "Core administrative role"
            },
            {
                "role_title": "Youth Minister",
                "setting": "Parish",
                "onet_code": "21-1021.00",
                "onet_title": "Child, Family, and School Social Workers",
                "mapping_notes": "Focus on youth programs"
            },
            {
                "role_title": "School Principal",
                "setting": "School",
                "onet_code": "11-9032.00",
                "onet_title": "Education Administrators, Kindergarten through Secondary",
                "mapping_notes": ""
            }
        ]
    
    @pytest.fixture
    def valid_csv_file(self, tmp_path, sample_csv_data):
        """Create a valid CSV file for testing."""
        csv_file = tmp_path / "test_roles.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(csv_file, index=False)
        return csv_file
    
    @pytest.fixture
    def csv_config(self, valid_csv_file):
        """Create CSV config for testing."""
        return CSVConfig(file_path=valid_csv_file)
    
    def test_load_valid_csv(self, csv_config, sample_csv_data):
        """Test loading valid CSV file."""
        loader = CSVLoader(csv_config)
        roles = loader.load_roles()
        
        assert len(roles) == 3
        assert all(isinstance(role, DiocesanRole) for role in roles)
        
        # Check first role
        first_role = roles[0]
        assert first_role.role_title == "Parish Secretary"
        assert first_role.setting == "Parish"
        assert first_role.onet_code == "43-6014.00"
    
    def test_missing_csv_file(self, tmp_path):
        """Test error handling for missing CSV file."""
        missing_file = tmp_path / "missing.csv"
        
        with pytest.raises(FileNotFoundError):
            config = CSVConfig(file_path=missing_file)
    
    def test_csv_missing_required_columns(self, tmp_path):
        """Test CSV with missing required columns."""
        csv_file = tmp_path / "incomplete.csv"
        
        # Create CSV missing 'setting' column
        df = pd.DataFrame({
            "role_title": ["Test Role"],
            "onet_code": ["43-6014.00"],
            "onet_title": ["Test Title"],
            "mapping_notes": [""]
        })
        df.to_csv(csv_file, index=False)
        
        config = CSVConfig(file_path=csv_file)
        loader = CSVLoader(config)
        
        with pytest.raises(ValueError, match="CSV missing required columns"):
            loader.load_roles()
    
    def test_csv_with_invalid_rows(self, tmp_path):
        """Test CSV with some invalid rows."""
        csv_file = tmp_path / "invalid_rows.csv"
        
        # Create CSV with one invalid O*NET code
        df = pd.DataFrame({
            "role_title": ["Valid Role", "Invalid Role"],
            "setting": ["Parish", "Parish"],
            "onet_code": ["43-6014.00", "invalid"],
            "onet_title": ["Valid Title", "Invalid Title"],
            "mapping_notes": ["", ""]
        })
        df.to_csv(csv_file, index=False)
        
        config = CSVConfig(file_path=csv_file)
        loader = CSVLoader(config)
        
        roles = loader.load_roles()
        assert len(roles) == 1  # Only valid role should be loaded
        assert roles[0].role_title == "Valid Role"
    
    def test_empty_csv_file(self, tmp_path):
        """Test empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        config = CSVConfig(file_path=csv_file)
        loader = CSVLoader(config)
        
        with pytest.raises(ValueError, match="CSV file is empty"):
            loader.load_roles()
    
    def test_get_unique_onet_codes(self, csv_config):
        """Test getting unique O*NET codes."""
        loader = CSVLoader(csv_config)
        roles = loader.load_roles()
        
        unique_codes = loader.get_unique_onet_codes(roles)
        assert len(unique_codes) == 3
        assert "43-6014.00" in unique_codes
        assert "21-1021.00" in unique_codes
        assert "11-9032.00" in unique_codes
    
    def test_get_unique_onet_codes_with_duplicates(self, tmp_path):
        """Test getting unique O*NET codes with duplicates."""
        csv_file = tmp_path / "duplicates.csv"
        
        # Create CSV with duplicate O*NET codes
        df = pd.DataFrame({
            "role_title": ["Role 1", "Role 2", "Role 3"],
            "setting": ["Parish", "Parish", "School"],
            "onet_code": ["43-6014.00", "43-6014.00", "21-1021.00"],
            "onet_title": ["Title 1", "Title 1", "Title 2"],
            "mapping_notes": ["", "", ""]
        })
        df.to_csv(csv_file, index=False)
        
        config = CSVConfig(file_path=csv_file)
        loader = CSVLoader(config)
        roles = loader.load_roles()
        
        unique_codes = loader.get_unique_onet_codes(roles)
        assert len(unique_codes) == 2  # Only 2 unique codes
        assert sorted(unique_codes) == ["21-1021.00", "43-6014.00"]
    
    def test_group_roles_by_onet_code(self, csv_config):
        """Test grouping roles by O*NET code."""
        loader = CSVLoader(csv_config)
        roles = loader.load_roles()
        
        grouped = loader.group_roles_by_onet_code(roles)
        
        assert len(grouped) == 3
        assert "43-6014.00" in grouped
        assert "21-1021.00" in grouped
        assert "11-9032.00" in grouped
        
        # Each group should have one role
        for code, role_list in grouped.items():
            assert len(role_list) == 1
            assert isinstance(role_list[0], DiocesanRole)
    
    def test_validate_csv_structure_valid(self, csv_config):
        """Test CSV structure validation for valid file."""
        loader = CSVLoader(csv_config)
        validation = loader.validate_csv_structure()
        
        assert validation["valid"] is True
        assert len(validation["columns"]) == 5
        assert len(validation["missing_columns"]) == 0
        assert validation["row_count"] == 3
        assert len(validation["sample_data"]) <= 5
    
    def test_validate_csv_structure_invalid(self, tmp_path):
        """Test CSV structure validation for invalid file."""
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("invalid content")
        
        config = CSVConfig(file_path=csv_file)
        loader = CSVLoader(config)
        validation = loader.validate_csv_structure()
        
        assert validation["valid"] is False
        assert "error" in validation
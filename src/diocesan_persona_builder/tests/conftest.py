"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import Mock

from diocesan_persona_builder.core.config import Settings, ONetCredentials, APIConfig
from diocesan_persona_builder.core.csv_loader import DiocesanRole
from diocesan_persona_builder.core.onet_api import (
    ONetOccupationData,
    ONetSkill,
    ONetTask,
    ONetKnowledge
)


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        onet_username="testuser",
        onet_password="testpass"
    )


@pytest.fixture
def sample_diocesan_role():
    """Create a sample diocesan role."""
    return DiocesanRole(
        role_title="Parish Secretary",
        setting="Parish",
        onet_code="43-6014.00",
        onet_title="Secretaries and Administrative Assistants",
        mapping_notes="Core administrative role"
    )


@pytest.fixture
def sample_onet_data():
    """Create sample O*NET occupation data."""
    skills = [
        ONetSkill(
            element_id="2.A.1.a",
            element_name="Reading Comprehension",
            scale_id="IM",
            data_value=75.0
        ),
        ONetSkill(
            element_id="2.A.1.b",
            element_name="Active Listening",
            scale_id="IM",
            data_value=72.0
        )
    ]
    
    tasks = [
        ONetTask(
            task_id=1,
            task="Answer telephones and direct calls to appropriate individuals",
            task_type="Core"
        ),
        ONetTask(
            task_id=2,
            task="Greet visitors and determine whether they should be given access",
            task_type="Core"
        )
    ]
    
    knowledge = [
        ONetKnowledge(
            element_id="2.C.1.a",
            element_name="Administration and Management",
            scale_id="IM",
            data_value=60.0
        )
    ]
    
    return ONetOccupationData(
        onet_code="43-6014.00",
        title="Secretaries and Administrative Assistants",
        description="Perform routine administrative functions",
        skills=skills,
        tasks=tasks,
        knowledge=knowledge
    )


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content as string."""
    return """role_title,setting,onet_code,onet_title,mapping_notes
Parish Secretary,Parish,43-6014.00,Secretaries and Administrative Assistants,Core administrative role
Youth Minister,Parish,21-1021.00,Child Family and School Social Workers,Focus on youth programs
School Principal,School,11-9032.00,Education Administrators Kindergarten through Secondary,"""


@pytest.fixture
def create_test_csv(tmp_path):
    """Factory to create test CSV files."""
    def _create_csv(content: str, filename: str = "test.csv") -> Path:
        csv_file = tmp_path / filename
        csv_file.write_text(content)
        return csv_file
    return _create_csv


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    
    # Mock successful responses
    client.get_occupation.return_value = {
        "title": "Test Occupation",
        "description": "Test description"
    }
    
    client.get_skills.return_value = [
        ONetSkill(
            element_id="2.A.1.a",
            element_name="Reading Comprehension",
            scale_id="IM",
            data_value=75.0
        )
    ]
    
    client.get_tasks.return_value = [
        ONetTask(
            task_id=1,
            task="Test task",
            task_type="Core"
        )
    ]
    
    client.get_knowledge.return_value = []
    client.get_work_context.return_value = []
    client.get_work_styles.return_value = []
    
    client.fetch_complete_occupation_data.return_value = ONetOccupationData(
        onet_code="43-6014.00",
        title="Test Occupation",
        description="Test description",
        skills=client.get_skills.return_value,
        tasks=client.get_tasks.return_value
    )
    
    return client


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory with basic template."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    # Create a basic test template
    template_content = """# {{ role_title }}

## Setting: {{ setting }}

## O*NET Code: {{ onet_code }}

## Skills:
{% for skill in top_skills %}
- {{ skill.name }}: {{ skill.importance }}%
{% endfor %}

## Tasks:
{% for task in key_tasks %}
- {{ task }}
{% endfor %}
"""
    
    template_file = template_dir / "persona.md.j2"
    template_file.write_text(template_content)
    
    return template_dir


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Clean environment variables for testing."""
    # Remove any existing environment variables that might interfere
    env_vars_to_remove = [
        "ONET_USERNAME",
        "ONET_PASSWORD",
        "CSV_PATH",
        "LOG_LEVEL"
    ]
    
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
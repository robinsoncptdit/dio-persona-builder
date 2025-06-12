"""Tests for O*NET API client."""

import pytest
import requests
from unittest.mock import Mock, patch
from pydantic import ValidationError

from diocesan_persona_builder.core.onet_api import (
    ONetSkill,
    ONetTask,
    ONetKnowledge,
    ONetWorkContext,
    ONetWorkStyle,
    ONetOccupationData,
    ONetAPIClient
)
from diocesan_persona_builder.core.config import ONetCredentials, APIConfig


class TestONetModels:
    """Tests for O*NET data models."""
    
    def test_onet_skill_model(self):
        """Test ONetSkill model creation."""
        skill_data = {
            "element_id": "2.A.1.a",
            "element_name": "Reading Comprehension",
            "scale_id": "IM",
            "data_value": 75.0,
            "n": 100,
            "standard_error": 2.5
        }
        
        skill = ONetSkill(**skill_data)
        assert skill.element_id == "2.A.1.a"
        assert skill.element_name == "Reading Comprehension"
        assert skill.scale_id == "IM"
        assert skill.data_value == 75.0
        assert skill.n == 100
        assert skill.standard_error == 2.5
    
    def test_onet_task_model(self):
        """Test ONetTask model creation."""
        task_data = {
            "task_id": 1,
            "task": "Answer telephones and direct calls",
            "task_type": "Core"
        }
        
        task = ONetTask(**task_data)
        assert task.task_id == 1
        assert task.task == "Answer telephones and direct calls"
        assert task.task_type == "Core"
    
    def test_onet_knowledge_model(self):
        """Test ONetKnowledge model creation."""
        knowledge_data = {
            "element_id": "2.C.1.a",
            "element_name": "Administration and Management",
            "scale_id": "IM",
            "data_value": 60.0
        }
        
        knowledge = ONetKnowledge(**knowledge_data)
        assert knowledge.element_id == "2.C.1.a"
        assert knowledge.element_name == "Administration and Management"
        assert knowledge.scale_id == "IM"
        assert knowledge.data_value == 60.0
    
    def test_onet_occupation_data(self):
        """Test ONetOccupationData dataclass."""
        data = ONetOccupationData(
            onet_code="43-6014.00",
            title="Secretaries and Administrative Assistants",
            description="Test description"
        )
        
        assert data.onet_code == "43-6014.00"
        assert data.title == "Secretaries and Administrative Assistants"
        assert data.description == "Test description"
        assert len(data.skills) == 0
        assert len(data.tasks) == 0


class TestONetAPIClient:
    """Tests for ONetAPIClient class."""
    
    @pytest.fixture
    def credentials(self):
        """Test credentials."""
        return ONetCredentials(username="testuser", password="testpass")
    
    @pytest.fixture
    def api_config(self):
        """Test API configuration."""
        return APIConfig(
            base_url="https://test.api.com",
            timeout=10,
            rate_limit_delay=0.1
        )
    
    @pytest.fixture
    def api_client(self, credentials, api_config):
        """Create API client for testing."""
        return ONetAPIClient(credentials, api_config)
    
    def test_client_initialization(self, api_client, credentials, api_config):
        """Test API client initialization."""
        assert api_client.credentials == credentials
        assert api_client.config == api_config
        assert api_client.session.auth == credentials.auth_tuple
        assert "application/json" in api_client.session.headers["Accept"]
    
    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep, api_client):
        """Test rate limiting functionality."""
        # First call should not sleep
        api_client._rate_limit()
        mock_sleep.assert_not_called()
        
        # Second call should sleep if within rate limit window
        import time
        api_client._last_request_time = time.time()
        api_client._rate_limit()
        mock_sleep.assert_called_once()
    
    @patch('diocesan_persona_builder.core.onet_api.requests.Session.get')
    def test_make_request_success(self, mock_get, api_client):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        result = api_client._make_request("test/endpoint")
        
        assert result == {"test": "data"}
        mock_get.assert_called_once()
    
    @patch('diocesan_persona_builder.core.onet_api.requests.Session.get')
    def test_make_request_http_error(self, mock_get, api_client):
        """Test API request with HTTP error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("Not found")
        mock_get.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            api_client._make_request("test/endpoint")
    
    @patch('diocesan_persona_builder.core.onet_api.requests.Session.get')
    @patch('time.sleep')
    def test_make_request_rate_limited(self, mock_sleep, mock_get, api_client):
        """Test API request with rate limiting."""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "2"}
        mock_get.return_value = mock_response
        
        with pytest.raises(requests.RequestException):
            api_client._make_request("test/endpoint")
        
        mock_sleep.assert_called_with(2)
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient._make_request')
    def test_get_occupation(self, mock_request, api_client):
        """Test get occupation information."""
        mock_request.return_value = {"title": "Test Occupation"}
        
        result = api_client.get_occupation("43-6014.00")
        
        assert result == {"title": "Test Occupation"}
        mock_request.assert_called_with("online/occupations/43-6014.00")
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient._make_request')
    def test_get_skills(self, mock_request, api_client):
        """Test get skills for occupation."""
        mock_response = {
            "element": [
                {
                    "element_id": "2.A.1.a",
                    "element_name": "Reading Comprehension", 
                    "scale_id": "IM",
                    "data_value": 75.0
                }
            ]
        }
        mock_request.return_value = mock_response
        
        skills = api_client.get_skills("43-6014.00")
        
        assert len(skills) == 1
        assert isinstance(skills[0], ONetSkill)
        assert skills[0].element_name == "Reading Comprehension"
        mock_request.assert_called_with("online/occupations/43-6014.00/skills")
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient._make_request')
    def test_get_tasks(self, mock_request, api_client):
        """Test get tasks for occupation."""
        mock_response = {
            "task": [
                {
                    "task_id": 1,
                    "task": "Answer telephones",
                    "task_type": "Core"
                }
            ]
        }
        mock_request.return_value = mock_response
        
        tasks = api_client.get_tasks("43-6014.00")
        
        assert len(tasks) == 1
        assert isinstance(tasks[0], ONetTask)
        assert tasks[0].task == "Answer telephones"
        mock_request.assert_called_with("online/occupations/43-6014.00/tasks")
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient._make_request')
    def test_get_knowledge(self, mock_request, api_client):
        """Test get knowledge for occupation."""
        mock_response = {
            "element": [
                {
                    "element_id": "2.C.1.a",
                    "element_name": "Administration and Management",
                    "scale_id": "IM", 
                    "data_value": 60.0
                }
            ]
        }
        mock_request.return_value = mock_response
        
        knowledge = api_client.get_knowledge("43-6014.00")
        
        assert len(knowledge) == 1
        assert isinstance(knowledge[0], ONetKnowledge)
        assert knowledge[0].element_name == "Administration and Management"
        mock_request.assert_called_with("online/occupations/43-6014.00/knowledge")
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_occupation')
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_skills')
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_tasks')
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_knowledge')
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_work_context')
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient.get_work_styles')
    def test_fetch_complete_occupation_data(
        self,
        mock_work_styles,
        mock_work_context,
        mock_knowledge,
        mock_tasks,
        mock_skills,
        mock_occupation,
        api_client
    ):
        """Test fetching complete occupation data."""
        # Mock all API responses
        mock_occupation.return_value = {
            "title": "Test Occupation",
            "description": "Test description"
        }
        mock_skills.return_value = [
            ONetSkill(
                element_id="2.A.1.a",
                element_name="Reading",
                scale_id="IM",
                data_value=75.0
            )
        ]
        mock_tasks.return_value = [
            ONetTask(task_id=1, task="Test task", task_type="Core")
        ]
        mock_knowledge.return_value = []
        mock_work_context.return_value = []
        mock_work_styles.return_value = []
        
        result = api_client.fetch_complete_occupation_data("43-6014.00")
        
        assert isinstance(result, ONetOccupationData)
        assert result.onet_code == "43-6014.00"
        assert result.title == "Test Occupation"
        assert result.description == "Test description"
        assert len(result.skills) == 1
        assert len(result.tasks) == 1
        
        # Verify all methods were called
        mock_occupation.assert_called_with("43-6014.00")
        mock_skills.assert_called_with("43-6014.00")
        mock_tasks.assert_called_with("43-6014.00")
        mock_knowledge.assert_called_with("43-6014.00")
        mock_work_context.assert_called_with("43-6014.00")
        mock_work_styles.assert_called_with("43-6014.00")
    
    @patch('diocesan_persona_builder.core.onet_api.ONetAPIClient._make_request')
    def test_api_error_handling(self, mock_request, api_client):
        """Test API error handling in data parsing."""
        # Mock response with invalid data
        mock_response = {
            "element": [
                {
                    "invalid_field": "invalid_data"  # Missing required fields
                }
            ]
        }
        mock_request.return_value = mock_response
        
        # Should handle parsing errors gracefully
        skills = api_client.get_skills("43-6014.00")
        assert len(skills) == 0  # Invalid data should be filtered out
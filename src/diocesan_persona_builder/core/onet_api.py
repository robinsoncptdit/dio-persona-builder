"""O*NET Web Services API client with retry logic and rate limiting."""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
from pydantic import BaseModel, Field

from .config import ONetCredentials, APIConfig
from .exceptions import (
    ONetError,
    ONetConnectionError,
    ONetAPIError,
    ONetDataError
)


logger = logging.getLogger(__name__)


class ONetSkill(BaseModel):
    """O*NET Skill data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="IM")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access to the O*NET data
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetTask(BaseModel):
    """O*NET Task data model."""
    
    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)  # This will be the task name/description
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="IM")
    task_type: Optional[str] = Field(None)
    green: Optional[bool] = Field(None)
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def task_id(self) -> int:
        return self.id
    
    @property
    def task(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetKnowledge(BaseModel):
    """O*NET Knowledge data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="IM")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetWorkContext(BaseModel):
    """O*NET Work Context data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="CX")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetWorkStyle(BaseModel):
    """O*NET Work Style data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="IM")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetAbility(BaseModel):
    """O*NET Ability data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="IM")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetPersonality(BaseModel):
    """O*NET Personality/Interest data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="OI")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetTechnology(BaseModel):
    """O*NET Technology data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    commodity_code: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


class ONetEducation(BaseModel):
    """O*NET Education data model."""
    
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    scale_id: str = Field(default="RL")
    n: Optional[int] = Field(None)
    standard_error: Optional[float] = Field(None)
    
    # Provide friendly access
    @property
    def element_id(self) -> str:
        return self.id
    
    @property
    def element_name(self) -> str:
        return self.name
    
    @property
    def data_value(self) -> float:
        return self.value
    
    class Config:
        extra = "ignore"


@dataclass
class ONetOccupationData:
    """Complete occupation data from O*NET."""
    
    onet_code: str
    title: str
    description: str = ""
    skills: List[ONetSkill] = field(default_factory=list)
    tasks: List[ONetTask] = field(default_factory=list)
    knowledge: List[ONetKnowledge] = field(default_factory=list)
    work_context: List[ONetWorkContext] = field(default_factory=list)
    work_styles: List[ONetWorkStyle] = field(default_factory=list)
    abilities: List[ONetAbility] = field(default_factory=list)
    personality: List[ONetPersonality] = field(default_factory=list)
    technology: List[ONetTechnology] = field(default_factory=list)
    education: List[ONetEducation] = field(default_factory=list)


class ONetAPIClient:
    """Client for O*NET Web Services API with retry logic and rate limiting."""
    
    def __init__(self, credentials: ONetCredentials, config: APIConfig):
        """Initialize the API client.
        
        Args:
            credentials: O*NET API credentials
            config: API configuration settings
        """
        self.credentials = credentials
        self.config = config
        self.session = requests.Session()
        self.session.auth = credentials.auth_tuple
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "diocesan-persona-builder/0.1.0"
        })
        # Disable SSL verification for O*NET API (common issue)
        self.session.verify = False
        # Suppress urllib3 SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self._last_request_time = 0.0
    
    def _rate_limit(self) -> None:
        """Implement rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((
            requests.RequestException, 
            requests.Timeout,
            requests.ConnectionError,
            requests.HTTPError
        )),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.INFO)
    )
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request with retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            ONetConnectionError: On connection issues
            ONetAPIError: On API errors (auth, not found, etc.)
            ONetDataError: On data parsing issues
        """
        self._rate_limit()
        
        url = f"{self.config.base_url}/{endpoint}"
        logger.debug(f"Making request to {url} with params {params}")
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout
            )
        except requests.ConnectionError as e:
            raise ONetConnectionError(f"Cannot connect to O*NET API at {url}") from e
        except requests.Timeout as e:
            raise ONetConnectionError(f"Timeout connecting to O*NET API (>{self.config.timeout}s)") from e
        except requests.RequestException as e:
            raise ONetConnectionError(f"Network error contacting O*NET API: {e}") from e
        
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
            time.sleep(retry_after)
            raise ONetAPIError("Rate limited by O*NET API", status_code=429, response_body=response.text)
        
        # Log the response for debugging
        logger.info(f"Response status: {response.status_code} for {url}")
        
        if response.status_code == 401:
            logger.error(f"Authentication failed for {url} - check credentials")
            raise ONetAPIError(
                "Authentication failed - check O*NET username/password in .env file",
                status_code=401,
                response_body=response.text
            )
        elif response.status_code == 404:
            logger.error(f"Endpoint not found: {url}")
            raise ONetAPIError(
                f"O*NET occupation code not found: {endpoint}",
                status_code=404,
                response_body=response.text
            )
        elif response.status_code >= 500:
            raise ONetAPIError(
                f"O*NET API server error: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text
            )
        elif response.status_code >= 400:
            raise ONetAPIError(
                f"O*NET API client error: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text
            )
        
        try:
            return response.json()
        except ValueError as e:
            raise ONetDataError(f"Invalid JSON response from O*NET API: {e}") from e
    
    def get_occupation(self, onet_code: str) -> Dict[str, Any]:
        """Get basic occupation information.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            Occupation data
        """
        endpoint = f"online/occupations/{onet_code}"
        return self._make_request(endpoint)
    
    def get_skills(self, onet_code: str) -> List[ONetSkill]:
        """Get skills for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of skills
        """
        endpoint = f"online/occupations/{onet_code}/details/skills"
        data = self._make_request(endpoint)
        
        skills = []
        for item in data.get("element", []):
            try:
                # Map the actual API response structure
                skill_data = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "IM",
                    "n": None,
                    "standard_error": None
                }
                skill = ONetSkill(**skill_data)
                skills.append(skill)
            except Exception as e:
                logger.error(f"Error parsing skill data: {e}")
                
        return skills
    
    def get_tasks(self, onet_code: str) -> List[ONetTask]:
        """Get tasks for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of tasks
        """
        endpoint = f"online/occupations/{onet_code}/details/tasks"
        data = self._make_request(endpoint)
        
        tasks = []
        for item in data.get("task", []):
            try:
                # Map the actual API response structure
                task_data = {
                    "id": item.get("id"),
                    "name": item.get("statement"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "IM",
                    "task_type": item.get("category"),
                    "green": item.get("green"),
                    "n": None,
                    "standard_error": None
                }
                task = ONetTask(**task_data)
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error parsing task data: {e}")
                
        return tasks
    
    def get_knowledge(self, onet_code: str) -> List[ONetKnowledge]:
        """Get knowledge areas for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of knowledge areas
        """
        endpoint = f"online/occupations/{onet_code}/details/knowledge"
        data = self._make_request(endpoint)
        
        knowledge_areas = []
        for item in data.get("element", []):
            try:
                # Map the actual API response structure
                knowledge_data = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "IM",
                    "n": None,
                    "standard_error": None
                }
                knowledge = ONetKnowledge(**knowledge_data)
                knowledge_areas.append(knowledge)
            except Exception as e:
                logger.error(f"Error parsing knowledge data: {e}")
                
        return knowledge_areas
    
    def get_work_context(self, onet_code: str) -> List[ONetWorkContext]:
        """Get work context for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of work context items
        """
        endpoint = f"online/occupations/{onet_code}/details/work_context"
        data = self._make_request(endpoint)
        
        contexts = []
        for item in data.get("element", []):
            try:
                context = ONetWorkContext(**item)
                contexts.append(context)
            except Exception as e:
                logger.error(f"Error parsing work context data: {e}")
                
        return contexts
    
    def get_work_styles(self, onet_code: str) -> List[ONetWorkStyle]:
        """Get work styles for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of work styles
        """
        endpoint = f"online/occupations/{onet_code}/details/work_styles"
        data = self._make_request(endpoint)
        
        styles = []
        for item in data.get("element", []):
            try:
                # Map the actual API response structure
                style_data = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "IM",
                    "n": None,
                    "standard_error": None
                }
                style = ONetWorkStyle(**style_data)
                styles.append(style)
            except Exception as e:
                logger.error(f"Error parsing work style data: {e}")
                
        return styles
    
    def get_abilities(self, onet_code: str) -> List[ONetAbility]:
        """Get abilities for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of abilities
        """
        endpoint = f"online/occupations/{onet_code}/details/abilities"
        data = self._make_request(endpoint)
        
        abilities = []
        for item in data.get("element", []):
            try:
                # Map the actual API response structure
                ability_data = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "IM",
                    "n": None,
                    "standard_error": None
                }
                ability = ONetAbility(**ability_data)
                abilities.append(ability)
            except Exception as e:
                logger.error(f"Error parsing ability data: {e}")
                
        return abilities
    
    def get_personality(self, onet_code: str) -> List[ONetPersonality]:
        """Get personality/interests for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of personality traits/interests
        """
        endpoint = f"online/occupations/{onet_code}/details/interests"
        data = self._make_request(endpoint)
        
        personalities = []
        for item in data.get("element", []):
            try:
                # Map the actual API response structure
                personality_data = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "OI",
                    "n": None,
                    "standard_error": None
                }
                personality = ONetPersonality(**personality_data)
                personalities.append(personality)
            except Exception as e:
                logger.error(f"Error parsing personality data: {e}")
                
        return personalities
    
    def get_technology(self, onet_code: str) -> List[ONetTechnology]:
        """Get technology skills for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of technology skills
        """
        endpoint = f"online/occupations/{onet_code}/details/technology_skills"
        data = self._make_request(endpoint)
        
        technologies = []
        
        # Collect all technologies from all categories for OpenAI filtering
        for category in data.get("category", []):
            category_name = category.get("title", {}).get("name", "")
            
            for item in category.get("example", []):
                try:
                    # Map the technology item structure
                    tech_data = {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "value": None,  # Technology doesn't have importance scores
                        "commodity_code": item.get("commodity_code"),
                        "category": category_name
                    }
                    technology = ONetTechnology(**tech_data)
                    technologies.append(technology)
                        
                except Exception as e:
                    logger.error(f"Error parsing technology data: {e}")
        
        return technologies
    
    def get_education(self, onet_code: str) -> List[ONetEducation]:
        """Get education requirements for an occupation.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            List of education requirements
        """
        endpoint = f"online/occupations/{onet_code}/details/education"
        data = self._make_request(endpoint)
        
        education_requirements = []
        # Education has a different structure with level_required
        for item in data.get("level_required", []):
            try:
                # Map the education item structure
                edu_data = {
                    "id": item.get("id"),
                    "name": item.get("category"),
                    "value": item.get("score", {}).get("value"),
                    "scale_id": "RL",
                    "n": None,
                    "standard_error": None
                }
                education = ONetEducation(**edu_data)
                education_requirements.append(education)
            except Exception as e:
                logger.error(f"Error parsing education data: {e}")
                
        return education_requirements
    
    def fetch_complete_occupation_data(self, onet_code: str) -> ONetOccupationData:
        """Fetch all occupation data for a given O*NET code.
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            Complete occupation data
        """
        logger.info(f"Fetching complete data for occupation {onet_code}")
        
        # Get basic occupation info
        occupation_info = self.get_occupation(onet_code)
        
        # Create occupation data object
        occupation_data = ONetOccupationData(
            onet_code=onet_code,
            title=occupation_info.get("title", ""),
            description=occupation_info.get("description", "")
        )
        
        # Fetch all data types
        try:
            occupation_data.skills = self.get_skills(onet_code)
            logger.debug(f"Fetched {len(occupation_data.skills)} skills")
        except Exception as e:
            logger.error(f"Error fetching skills for {onet_code}: {e}")
        
        try:
            occupation_data.tasks = self.get_tasks(onet_code)
            logger.debug(f"Fetched {len(occupation_data.tasks)} tasks")
        except Exception as e:
            logger.error(f"Error fetching tasks for {onet_code}: {e}")
        
        try:
            occupation_data.knowledge = self.get_knowledge(onet_code)
            logger.debug(f"Fetched {len(occupation_data.knowledge)} knowledge areas")
        except Exception as e:
            logger.error(f"Error fetching knowledge for {onet_code}: {e}")
        
        try:
            occupation_data.work_context = self.get_work_context(onet_code)
            logger.debug(f"Fetched {len(occupation_data.work_context)} work context items")
        except Exception as e:
            logger.error(f"Error fetching work context for {onet_code}: {e}")
        
        try:
            occupation_data.work_styles = self.get_work_styles(onet_code)
            logger.debug(f"Fetched {len(occupation_data.work_styles)} work styles")
        except Exception as e:
            logger.error(f"Error fetching work styles for {onet_code}: {e}")
        
        try:
            occupation_data.abilities = self.get_abilities(onet_code)
            logger.debug(f"Fetched {len(occupation_data.abilities)} abilities")
        except Exception as e:
            logger.error(f"Error fetching abilities for {onet_code}: {e}")
        
        try:
            occupation_data.personality = self.get_personality(onet_code)
            logger.debug(f"Fetched {len(occupation_data.personality)} personality traits")
        except Exception as e:
            logger.error(f"Error fetching personality for {onet_code}: {e}")
        
        try:
            occupation_data.technology = self.get_technology(onet_code)
            logger.debug(f"Fetched {len(occupation_data.technology)} technology skills")
        except Exception as e:
            logger.error(f"Error fetching technology for {onet_code}: {e}")
        
        try:
            occupation_data.education = self.get_education(onet_code)
            logger.debug(f"Fetched {len(occupation_data.education)} education requirements")
        except Exception as e:
            logger.error(f"Error fetching education for {onet_code}: {e}")
        
        return occupation_data
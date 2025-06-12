"""Template engine for generating persona markdown files."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError

from .csv_loader import DiocesanRole
from .onet_api import ONetOccupationData, ONetSkill, ONetKnowledge, ONetAbility, ONetPersonality, ONetTechnology, ONetEducation
from .technology_filter import TechnologyFilter


logger = logging.getLogger(__name__)


class PersonaData:
    """Container for persona template data."""
    
    def __init__(self, role: DiocesanRole, onet_data: ONetOccupationData, technology_filter: Optional[TechnologyFilter] = None):
        """Initialize persona data.
        
        Args:
            role: Diocesan role information
            onet_data: O*NET occupation data
            technology_filter: Shared technology filter instance for persona-specific recommendations
        """
        self.role = role
        self.onet_data = onet_data
        self.generated_at = datetime.utcnow()
        self.tech_filter = technology_filter or TechnologyFilter(api_key=None)
    
    def get_top_skills(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top skills sorted by importance.
        
        Args:
            limit: Maximum number of skills to return
            
        Returns:
            List of skill dictionaries
        """
        # Filter skills by importance scale (IM = Importance)
        importance_skills = [
            s for s in self.onet_data.skills 
            if s.scale_id == "IM"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_skills = sorted(
            importance_skills,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": skill.element_name or "Unknown Skill",
                "importance": skill.data_value or 0,
                "importance_label": self._get_importance_label(skill.data_value or 0)
            }
            for skill in sorted_skills
            if skill.element_name is not None
        ]
    
    def get_top_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top knowledge areas sorted by importance.
        
        Args:
            limit: Maximum number of knowledge areas to return
            
        Returns:
            List of knowledge dictionaries
        """
        # Filter knowledge by importance scale
        importance_knowledge = [
            k for k in self.onet_data.knowledge
            if k.scale_id == "IM"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_knowledge = sorted(
            importance_knowledge,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": knowledge.element_name or "Unknown Knowledge",
                "importance": knowledge.data_value or 0,
                "importance_label": self._get_importance_label(knowledge.data_value or 0)
            }
            for knowledge in sorted_knowledge
            if knowledge.element_name is not None
        ]
    
    def get_key_tasks(self, limit: int = 10) -> List[str]:
        """Get key tasks for the role.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of task descriptions
        """
        # Core tasks are typically more important
        core_tasks = [
            t.task for t in self.onet_data.tasks
            if t.task is not None and (t.task_type == "Core" or not t.task_type)
        ][:limit]
        
        # If not enough core tasks, add supplemental
        if len(core_tasks) < limit:
            supplemental_tasks = [
                t.task for t in self.onet_data.tasks
                if t.task is not None and t.task_type == "Supplemental"
            ][:(limit - len(core_tasks))]
            core_tasks.extend(supplemental_tasks)
        
        return core_tasks
    
    def get_work_context_highlights(self) -> Dict[str, Any]:
        """Get notable work context elements.
        
        Returns:
            Dictionary of work context highlights
        """
        context_map = {
            "contact_with_others": [],
            "work_schedule": [],
            "physical_proximity": [],
            "work_setting": []
        }
        
        for context in self.onet_data.work_context:
            if context.element_name is None or context.data_value is None:
                continue
            name_lower = context.element_name.lower()
            
            if "contact" in name_lower or "interact" in name_lower:
                context_map["contact_with_others"].append({
                    "name": context.element_name,
                    "value": context.data_value
                })
            elif "schedule" in name_lower or "hours" in name_lower:
                context_map["work_schedule"].append({
                    "name": context.element_name,
                    "value": context.data_value
                })
            elif "proximity" in name_lower or "close" in name_lower:
                context_map["physical_proximity"].append({
                    "name": context.element_name,
                    "value": context.data_value
                })
            elif "indoor" in name_lower or "outdoor" in name_lower or "setting" in name_lower:
                context_map["work_setting"].append({
                    "name": context.element_name,
                    "value": context.data_value
                })
        
        return context_map
    
    def get_work_styles_summary(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Get work styles sorted by importance.
        
        Args:
            limit: Maximum number of work styles to return
            
        Returns:
            List of work style dictionaries
        """
        # Filter work styles by importance scale
        importance_styles = [
            s for s in self.onet_data.work_styles
            if s.scale_id == "IM"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_styles = sorted(
            importance_styles,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": style.element_name or "Unknown Style",
                "importance": style.data_value or 0,
                "description": self._get_work_style_description(style.element_name or "")
            }
            for style in sorted_styles
            if style.element_name is not None
        ]
    
    def get_top_abilities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top abilities sorted by importance.
        
        Args:
            limit: Maximum number of abilities to return
            
        Returns:
            List of ability dictionaries
        """
        # Filter abilities by importance scale
        importance_abilities = [
            a for a in self.onet_data.abilities
            if a.scale_id == "IM"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_abilities = sorted(
            importance_abilities,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": ability.element_name or "Unknown Ability",
                "importance": ability.data_value or 0,
                "importance_label": self._get_importance_label(ability.data_value or 0)
            }
            for ability in sorted_abilities
            if ability.element_name is not None
        ]
    
    def get_personality_traits(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Get personality traits and interests sorted by importance.
        
        Args:
            limit: Maximum number of traits to return
            
        Returns:
            List of personality trait dictionaries
        """
        # Filter personality by relevance scale (OI = Occupational Interest)
        interest_traits = [
            p for p in self.onet_data.personality
            if p.scale_id == "OI"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_traits = sorted(
            interest_traits,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": trait.element_name or "Unknown Trait",
                "importance": trait.data_value or 0,
                "importance_label": self._get_importance_label(trait.data_value or 0)
            }
            for trait in sorted_traits
            if trait.element_name is not None
        ]
    
    def get_technology_skills(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Get technology skills for the role, filtered by relevance.
        
        Args:
            limit: Maximum number of technology skills to return
            
        Returns:
            List of technology skill dictionaries
        """
        # Get all technology names
        all_tech_names = [
            tech.element_name
            for tech in self.onet_data.technology
            if tech.element_name is not None
        ]
        
        if not all_tech_names:
            return []
        
        # Filter using OpenAI if available
        filtered_tech_names = self.tech_filter.filter_technologies(
            role_title=self.role.role_title,
            role_setting=self.role.setting,
            technologies=all_tech_names,
            max_items=limit
        )
        
        # Convert back to dictionaries
        tech_skills = [
            {
                "name": tech_name,
                "importance": None  # Technology doesn't have importance scores
            }
            for tech_name in filtered_tech_names
        ]
        
        return tech_skills
    
    def get_education_requirements(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Get education requirements sorted by importance.
        
        Args:
            limit: Maximum number of education requirements to return
            
        Returns:
            List of education requirement dictionaries
        """
        # Filter education by relevance scale (RL = Required Level)
        relevant_education = [
            e for e in self.onet_data.education
            if e.scale_id == "RL"
        ]
        
        # Sort by data_value descending, handling None values
        sorted_education = sorted(
            relevant_education,
            key=lambda x: x.data_value if x.data_value is not None else 0,
            reverse=True
        )[:limit]
        
        return [
            {
                "name": edu.element_name or "Unknown Education",
                "importance": edu.data_value or 0,
                "importance_label": self._get_importance_label(edu.data_value or 0)
            }
            for edu in sorted_education
            if edu.element_name is not None
        ]
    
    def _get_importance_label(self, value: float) -> str:
        """Convert importance value to label.
        
        Args:
            value: Importance value (0-100)
            
        Returns:
            Importance label
        """
        if value >= 80:
            return "Extremely Important"
        elif value >= 65:
            return "Very Important"
        elif value >= 50:
            return "Important"
        elif value >= 35:
            return "Somewhat Important"
        else:
            return "Not Important"
    
    def _get_work_style_description(self, style_name: str) -> str:
        """Get a brief description for a work style.
        
        Args:
            style_name: Name of the work style
            
        Returns:
            Brief description
        """
        # Simple mapping - in a real application, this would be more comprehensive
        descriptions = {
            "Attention to Detail": "Careful attention to detail and thoroughness",
            "Dependability": "Reliable, responsible, and trustworthy",
            "Integrity": "Honest and ethical behavior",
            "Cooperation": "Pleasant with others and cooperative attitude",
            "Stress Tolerance": "Accepts criticism and deals calmly with stress",
            "Initiative": "Willingness to take on responsibilities",
            "Leadership": "Willingness to lead and offer direction",
            "Achievement/Effort": "Establishes and maintains challenging goals"
        }
        
        return descriptions.get(style_name, "Important work characteristic")
    
    def to_template_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering.
        
        Returns:
            Dictionary of template variables
        """
        return {
            "role_title": self.role.role_title,
            "setting": self.role.setting,
            "role_slug": self.role.role_slug,
            "onet_code": self.role.onet_code,
            "onet_title": self.role.onet_title,
            "mapping_notes": self.role.mapping_notes,
            "occupation_description": self.onet_data.description,
            "top_skills": self.get_top_skills(),
            "top_knowledge": self.get_top_knowledge(),
            "top_abilities": self.get_top_abilities(),
            "personality_traits": self.get_personality_traits(),
            "technology_skills": self.get_technology_skills(),
            "education_requirements": self.get_education_requirements(),
            "key_tasks": self.get_key_tasks(),
            "work_context": self.get_work_context_highlights(),
            "work_styles": self.get_work_styles_summary(),
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        }


class TemplateEngine:
    """Jinja2-based template engine for persona generation."""
    
    def __init__(self, template_dir: Path, technology_filter: Optional[TechnologyFilter] = None):
        """Initialize the template engine.
        
        Args:
            template_dir: Directory containing Jinja2 templates
            technology_filter: Shared technology filter for persona-specific recommendations
        """
        self.template_dir = template_dir
        self.technology_filter = technology_filter
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['round'] = lambda x, n=1: round(x, n)
        self.env.filters['percentage'] = lambda x: f"{x:.0f}%"
    
    def get_template(self, template_name: str = "persona.md.j2") -> Template:
        """Get a template by name.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Jinja2 Template object
            
        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name} in {self.template_dir}")
            raise
    
    def render_persona(
        self,
        role: DiocesanRole,
        onet_data: ONetOccupationData,
        template_name: str = "persona.md.j2",
        openai_api_key: Optional[str] = None  # Kept for backward compatibility
    ) -> str:
        """Render a persona to markdown.
        
        Args:
            role: Diocesan role
            onet_data: O*NET occupation data
            template_name: Template to use
            openai_api_key: OpenAI API key (deprecated, use shared technology_filter)
            
        Returns:
            Rendered markdown content
        """
        logger.info(f"Rendering persona for {role.role_title} using {template_name}")
        
        # Create persona data with shared technology filter for best persona-specific results
        persona_data = PersonaData(role, onet_data, self.technology_filter)
        
        # Get template
        template = self.get_template(template_name)
        
        # Render template
        try:
            content = template.render(**persona_data.to_template_dict())
            return content
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise
    
    def validate_template(self, template_name: str = "persona.md.j2") -> bool:
        """Validate that a template exists and has valid syntax.
        
        Args:
            template_name: Name of the template to validate
            
        Returns:
            True if template is valid
        """
        try:
            template = self.get_template(template_name)
            # Try to render with minimal data to check syntax
            template.render(
                role_title="Test Role",
                setting="Test Setting",
                onet_code="00-0000.00",
                onet_title="Test Title",
                mapping_notes="",
                occupation_description="Test description",
                top_skills=[],
                top_knowledge=[],
                top_abilities=[],
                personality_traits=[],
                technology_skills=[],
                education_requirements=[],
                key_tasks=[],
                work_context={},
                work_styles=[],
                generated_at="2024-01-01 00:00:00 UTC"
            )
            return True
        except (TemplateNotFound, TemplateSyntaxError) as e:
            logger.error(f"Template validation failed: {e}")
            return False
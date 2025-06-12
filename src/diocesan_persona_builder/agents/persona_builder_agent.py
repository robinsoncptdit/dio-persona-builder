"""Agent-based persona builder using CrewAI patterns."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from ..core.csv_loader import DiocesanRole, CSVLoader
from ..core.onet_api import ONetAPIClient, ONetOccupationData
from ..core.template_engine import TemplateEngine
from ..core.config import Settings


logger = logging.getLogger(__name__)


@dataclass
class PersonaBuildTask:
    """Task for building a persona."""
    
    role: DiocesanRole
    onet_data: Optional[ONetOccupationData] = None
    output_path: Optional[Path] = None
    status: str = "pending"  # pending, fetching, rendering, completed, failed
    error: Optional[str] = None


class PersonaBuilderAgent:
    """Agent responsible for coordinating persona building tasks."""
    
    def __init__(self, settings: Settings):
        """Initialize the persona builder agent.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_client = ONetAPIClient(
            credentials=settings.credentials,
            config=settings.api_config
        )
        self.template_engine = TemplateEngine(
            template_dir=Path(__file__).parent.parent.parent.parent / "templates"
        )
        self.tasks: List[PersonaBuildTask] = []
        self._onet_cache: Dict[str, ONetOccupationData] = {}
    
    def load_roles_from_csv(self, csv_path: Path) -> List[DiocesanRole]:
        """Load roles from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of diocesan roles
        """
        logger.info(f"Loading roles from {csv_path}")
        csv_config = self.settings.get_csv_config(csv_path)
        loader = CSVLoader(csv_config)
        
        roles = loader.load_roles()
        
        # Create tasks for each role
        self.tasks = [
            PersonaBuildTask(role=role)
            for role in roles
        ]
        
        logger.info(f"Created {len(self.tasks)} persona build tasks")
        return roles
    
    def fetch_onet_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch O*NET data for all unique occupation codes.
        
        Args:
            force_refresh: Force refresh even if data is cached
            
        Returns:
            Summary of fetch operation
        """
        logger.info("Starting O*NET data fetch")
        
        # Get unique O*NET codes
        unique_codes = list(set(task.role.onet_code for task in self.tasks))
        logger.info(f"Found {len(unique_codes)} unique O*NET codes to fetch")
        
        fetch_results = {
            "total": len(unique_codes),
            "success": 0,
            "failed": 0,
            "cached": 0,
            "errors": []
        }
        
        for code in unique_codes:
            if code in self._onet_cache and not force_refresh:
                fetch_results["cached"] += 1
                logger.debug(f"Using cached data for {code}")
                continue
            
            try:
                logger.info(f"Fetching data for O*NET code: {code}")
                onet_data = self.api_client.fetch_complete_occupation_data(code)
                self._onet_cache[code] = onet_data
                fetch_results["success"] += 1
                
                # Update tasks with fetched data
                for task in self.tasks:
                    if task.role.onet_code == code:
                        task.onet_data = onet_data
                        task.status = "fetched"
                        
            except Exception as e:
                logger.error(f"Failed to fetch data for {code}: {e}")
                fetch_results["failed"] += 1
                fetch_results["errors"].append({
                    "code": code,
                    "error": str(e)
                })
                
                # Mark affected tasks as failed
                for task in self.tasks:
                    if task.role.onet_code == code:
                        task.status = "failed"
                        task.error = f"Failed to fetch O*NET data: {e}"
        
        return fetch_results
    
    def generate_personas(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Generate persona markdown files.
        
        Args:
            output_dir: Output directory (uses config default if not provided)
            
        Returns:
            Summary of generation operation
        """
        output_path = output_dir or self.settings.output_config.output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating personas to {output_path}")
        
        generation_results = {
            "total": len(self.tasks),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for task in self.tasks:
            if task.status == "failed":
                generation_results["skipped"] += 1
                continue
            
            if not task.onet_data:
                generation_results["skipped"] += 1
                task.status = "failed"
                task.error = "No O*NET data available"
                continue
            
            try:
                # Generate persona content
                content = self.template_engine.render_persona(
                    role=task.role,
                    onet_data=task.onet_data,
                    openai_api_key=self.settings.openai_api_key
                )
                
                # Write to file
                filename = self.settings.output_config.file_pattern.format(
                    role_slug=task.role.role_slug
                )
                file_path = output_path / filename
                
                file_path.write_text(content, encoding='utf-8')
                
                task.output_path = file_path
                task.status = "completed"
                generation_results["success"] += 1
                
                logger.info(f"Generated persona: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to generate persona for {task.role.role_title}: {e}")
                task.status = "failed"
                task.error = f"Generation failed: {e}"
                generation_results["failed"] += 1
                generation_results["errors"].append({
                    "role": task.role.role_title,
                    "error": str(e)
                })
        
        return generation_results
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of all tasks.
        
        Returns:
            Task summary statistics
        """
        status_counts = {}
        for task in self.tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "status_breakdown": status_counts,
            "unique_onet_codes": len(set(task.role.onet_code for task in self.tasks)),
            "completed_personas": len([t for t in self.tasks if t.output_path]),
            "failed_tasks": [
                {
                    "role": t.role.role_title,
                    "error": t.error
                }
                for t in self.tasks if t.status == "failed"
            ]
        }
    
    def run_full_pipeline(self, csv_path: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Run the complete persona building pipeline.
        
        Args:
            csv_path: Path to input CSV
            output_dir: Output directory (optional)
            
        Returns:
            Complete pipeline results
        """
        logger.info("Starting full persona building pipeline")
        
        results = {
            "csv_load": {},
            "data_fetch": {},
            "generation": {},
            "summary": {}
        }
        
        try:
            # Load roles
            roles = self.load_roles_from_csv(csv_path)
            results["csv_load"] = {
                "success": True,
                "roles_loaded": len(roles)
            }
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            results["csv_load"] = {
                "success": False,
                "error": str(e)
            }
            return results
        
        # Fetch O*NET data
        results["data_fetch"] = self.fetch_onet_data()
        
        # Generate personas
        results["generation"] = self.generate_personas(output_dir)
        
        # Get final summary
        results["summary"] = self.get_task_summary()
        
        logger.info("Persona building pipeline completed")
        return results
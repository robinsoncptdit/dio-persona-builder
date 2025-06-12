"""CSV loader module for diocesan roles data."""

import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field, validator

from .config import CSVConfig


logger = logging.getLogger(__name__)


class DiocesanRole(BaseModel):
    """Model for a diocesan role from CSV."""
    
    role_title: str = Field(..., description="Title of the diocesan role")
    setting: str = Field(..., description="Work setting (e.g., Parish, School)")
    onet_code: str = Field(..., description="O*NET occupation code")
    onet_title: str = Field(..., description="O*NET occupation title")
    mapping_notes: str = Field(default="", description="Notes about the mapping")
    
    @validator("onet_code")
    def validate_onet_code(cls, v: str) -> str:
        """Validate O*NET code format."""
        # O*NET codes are typically in format XX-XXXX.XX
        if not v or len(v) < 7:
            raise ValueError(f"Invalid O*NET code format: {v}")
        return v.strip()
    
    @property
    def role_slug(self) -> str:
        """Generate a slug for the role suitable for filenames."""
        # Create a filesystem-safe slug from role title and setting
        slug = f"{self.role_title}_{self.setting}".lower()
        # Replace spaces and special characters
        slug = slug.replace(" ", "_")
        slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)
        # Remove consecutive underscores
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug.strip("_")


class CSVLoader:
    """Loader for diocesan roles CSV data."""
    
    def __init__(self, config: CSVConfig):
        """Initialize the CSV loader.
        
        Args:
            config: CSV configuration
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the CSV configuration."""
        if not self.config.file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.config.file_path}")
    
    def load_roles(self) -> List[DiocesanRole]:
        """Load diocesan roles from CSV.
        
        Returns:
            List of DiocesanRole objects
            
        Raises:
            ValueError: If CSV is invalid or missing required columns
        """
        logger.info(f"Loading roles from {self.config.file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(self.config.file_path, dtype=str)
            
            # Validate required columns
            missing_columns = set(self.config.required_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(
                    f"CSV missing required columns: {missing_columns}. "
                    f"Found columns: {list(df.columns)}"
                )
            
            # Fill NaN values with empty strings
            df = df.fillna("")
            
            # Convert to DiocesanRole objects
            roles = []
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    role = DiocesanRole(**row.to_dict())
                    roles.append(role)
                except Exception as e:
                    error_msg = f"Row {idx + 2}: {str(e)}"  # +2 for header and 0-indexing
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            if errors:
                logger.warning(f"Loaded {len(roles)} roles with {len(errors)} errors")
                if len(errors) > 5:
                    logger.warning(f"First 5 errors: {errors[:5]}")
                else:
                    logger.warning(f"Errors: {errors}")
            else:
                logger.info(f"Successfully loaded {len(roles)} roles")
            
            if not roles:
                raise ValueError("No valid roles found in CSV")
            
            return roles
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {self.config.file_path}")
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def get_unique_onet_codes(self, roles: List[DiocesanRole]) -> List[str]:
        """Get unique O*NET codes from roles.
        
        Args:
            roles: List of diocesan roles
            
        Returns:
            List of unique O*NET codes
        """
        onet_codes = list(set(role.onet_code for role in roles))
        logger.info(f"Found {len(onet_codes)} unique O*NET codes")
        return sorted(onet_codes)
    
    def group_roles_by_onet_code(self, roles: List[DiocesanRole]) -> Dict[str, List[DiocesanRole]]:
        """Group roles by their O*NET code.
        
        Args:
            roles: List of diocesan roles
            
        Returns:
            Dictionary mapping O*NET codes to lists of roles
        """
        grouped = {}
        for role in roles:
            if role.onet_code not in grouped:
                grouped[role.onet_code] = []
            grouped[role.onet_code].append(role)
        
        logger.info(f"Grouped {len(roles)} roles into {len(grouped)} O*NET codes")
        return grouped
    
    def validate_csv_structure(self) -> Dict[str, Any]:
        """Validate CSV structure and return summary.
        
        Returns:
            Dictionary with validation results
        """
        try:
            df = pd.read_csv(self.config.file_path, nrows=5)  # Read only first 5 rows for validation
            
            return {
                "valid": True,
                "columns": list(df.columns),
                "missing_columns": list(set(self.config.required_columns) - set(df.columns)),
                "extra_columns": list(set(df.columns) - set(self.config.required_columns)),
                "row_count": len(pd.read_csv(self.config.file_path)),
                "sample_data": df.to_dict("records")
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
"""Technology filtering using OpenAI to select relevant tools for specific roles."""

import logging
from typing import List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class TechnologyFilter:
    """Filter technology lists using OpenAI to select role-appropriate tools."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the technology filter.
        
        Args:
            api_key: OpenAI API key. If None, filtering will be skipped.
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def filter_technologies(self, role_title: str, role_setting: str, technologies: List[str], max_items: int = 8) -> List[str]:
        """Filter technology list to most relevant items for the role.
        
        Args:
            role_title: The job title (e.g., "Parish Secretary")
            role_setting: The work setting (e.g., "Parish")
            technologies: List of all available technologies
            max_items: Maximum number of technologies to return
            
        Returns:
            Filtered list of most relevant technologies
        """
        if not self.client or not technologies:
            # Fallback: return first N items if no OpenAI filtering
            return technologies[:max_items]
        
        try:
            # Create the prompt
            tech_list = "\n".join(f"- {tech}" for tech in technologies)
            
            prompt = f"""You are helping to create a technology profile for a job role. 

Job Title: {role_title}
Work Setting: {role_setting}

From the following list of technologies, select the top {max_items} that would be most commonly used by someone in this role. Focus on practical, everyday tools rather than specialized enterprise software unless truly relevant.

Available technologies:
{tech_list}

Please respond with ONLY the names of the selected technologies, one per line, no bullet points or numbering. Choose the most practical and commonly used tools for this role."""

            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent results
            )
            
            # Parse response
            filtered_technologies = []
            response_text = response.choices[0].message.content.strip()
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line and line in technologies:
                    filtered_technologies.append(line)
            
            # Ensure we have some results
            if filtered_technologies:
                logger.info(f"OpenAI filtered {len(technologies)} technologies to {len(filtered_technologies)} for {role_title}")
                return filtered_technologies[:max_items]
            else:
                logger.warning(f"OpenAI filtering returned no valid results for {role_title}, using fallback")
                return technologies[:max_items]
                
        except Exception as e:
            logger.error(f"Error filtering technologies with OpenAI: {e}")
            # Fallback to original list
            return technologies[:max_items]
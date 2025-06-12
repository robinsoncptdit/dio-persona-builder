"""Custom exception hierarchy for Diocesan Persona Builder."""

from typing import Optional, Any


class PersonaBuilderError(Exception):
    """Base exception for all persona builder errors."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ConfigurationError(PersonaBuilderError):
    """Raised when configuration is invalid or missing."""
    pass


class CSVError(PersonaBuilderError):
    """Base exception for CSV-related errors."""
    pass


class CSVValidationError(CSVError):
    """Raised when CSV file structure is invalid."""
    pass


class CSVParsingError(CSVError):
    """Raised when CSV file cannot be parsed."""
    pass


class ONetError(PersonaBuilderError):
    """Base exception for O*NET API-related errors."""
    pass


class ONetConnectionError(ONetError):
    """Raised when unable to connect to O*NET API."""
    pass


class ONetAPIError(ONetError):
    """Raised when O*NET API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ONetDataError(ONetError):
    """Raised when O*NET API returns invalid or unexpected data."""
    pass


class TemplateError(PersonaBuilderError):
    """Base exception for template-related errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template file cannot be found."""
    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""
    pass


class OpenAIError(PersonaBuilderError):
    """Base exception for OpenAI-related errors."""
    pass


class OpenAIConnectionError(OpenAIError):
    """Raised when unable to connect to OpenAI API."""
    pass


class OpenAIAPIError(OpenAIError):
    """Raised when OpenAI API returns an error response."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, error_type: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code
        self.error_type = error_type


class OpenAIQuotaError(OpenAIError):
    """Raised when OpenAI API quota is exceeded."""
    pass


class FileSystemError(PersonaBuilderError):
    """Base exception for file system operations."""
    pass


class OutputDirectoryError(FileSystemError):
    """Raised when output directory cannot be created or accessed."""
    pass


class PersonaFileError(FileSystemError):
    """Raised when persona files cannot be read or written."""
    pass
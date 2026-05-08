"""
Project-related data models.
Defines the structure for uploaded projects, file trees, and project metadata.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Status of a project analysis."""
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectType(str, Enum):
    """Detected project types."""
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    MICROSERVICE = "microservice"
    MONOLITH = "monolith"
    MOBILE_APP = "mobile_app"
    DATA_PIPELINE = "data_pipeline"
    UNKNOWN = "unknown"


class ArchitecturePattern(str, Enum):
    """Detected architecture patterns."""
    MVC = "mvc"
    CLEAN_ARCHITECTURE = "clean_architecture"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    PLUGIN = "plugin"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    UNKNOWN = "unknown"


class TechStackItem(BaseModel):
    """A detected technology in the project."""
    name: str
    version: Optional[str] = None
    category: str  # framework, language, database, build_tool, etc.
    confidence: float = 1.0


class FileNode(BaseModel):
    """A node in the project file tree."""
    name: str
    path: str
    is_directory: bool
    children: list["FileNode"] = []
    size: Optional[int] = None
    language: Optional[str] = None
    line_count: Optional[int] = None


class ProjectMetadata(BaseModel):
    """Detected project metadata."""
    name: str
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.UNKNOWN
    architecture_pattern: ArchitecturePattern = ArchitecturePattern.UNKNOWN
    tech_stack: list[TechStackItem] = []
    entry_points: list[str] = []
    total_files: int = 0
    total_lines: int = 0
    languages: dict[str, int] = {}  # language -> line count
    has_tests: bool = False
    has_docs: bool = False
    has_ci: bool = False
    has_docker: bool = False


class Project(BaseModel):
    """Represents an uploaded project."""
    id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.UPLOADING
    source_type: str = "zip"  # zip or github
    source_url: Optional[str] = None
    upload_path: Optional[str] = None
    metadata: Optional[ProjectMetadata] = None
    file_tree: Optional[FileNode] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class ProjectUploadResponse(BaseModel):
    """Response after project upload."""
    project_id: str
    status: ProjectStatus
    message: str


class ProjectSummary(BaseModel):
    """Summary of a project for listing."""
    id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    project_type: ProjectType = ProjectType.UNKNOWN
    total_files: int = 0
    created_at: datetime

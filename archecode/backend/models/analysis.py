"""
Analysis result data models.
Defines structures for code analysis outputs including bugs, dead code, tech debt, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    """Severity levels for analysis findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Categories of analysis findings."""
    BUG = "bug"
    DEAD_CODE = "dead_code"
    TECH_DEBT = "tech_debt"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MAGIC_NUMBER = "magic_number"
    NAMING = "naming"
    DEPRECATED = "deprecated"


class CodeLocation(BaseModel):
    """Location of a finding in source code."""
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    code_snippet: Optional[str] = None


class AnalysisFinding(BaseModel):
    """A single analysis finding."""
    id: str
    category: FindingCategory
    severity: Severity
    title: str
    description: str
    location: Optional[CodeLocation] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    confidence: float = 1.0


class ModuleDependency(BaseModel):
    """Represents a dependency between two modules."""
    source: str
    target: str
    dependency_type: str  # import, call, inheritance, composition
    weight: float = 1.0


class FunctionInfo(BaseModel):
    """Information about a function or method."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    parameters: list[str] = []
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    complexity: Optional[int] = None
    is_exported: bool = False
    callers: list[str] = []
    callees: list[str] = []


class ClassInfo(BaseModel):
    """Information about a class."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods: list[FunctionInfo] = []
    base_classes: list[str] = []
    attributes: list[str] = []
    docstring: Optional[str] = None


class SecurityIssue(BaseModel):
    """A security vulnerability found in the code."""
    id: str
    title: str
    description: str
    severity: Severity
    location: CodeLocation
    cwe_id: Optional[str] = None
    recommendation: str


class AnalysisResult(BaseModel):
    """Complete analysis result for a project."""
    project_id: str
    id: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Summary
    summary: str = ""
    project_type: str = ""
    architecture_pattern: str = ""

    # Findings
    findings: list[AnalysisFinding] = []
    security_issues: list[SecurityIssue] = []

    # Code structure
    dependencies: list[ModuleDependency] = []
    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []

    # Metrics
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    overall_health_score: float = 100.0

    # AI Generated
    readme_content: Optional[str] = None
    api_docs: Optional[str] = None
    architecture_description: Optional[str] = None
    refactoring_suggestions: list[str] = []


class AnalysisRequest(BaseModel):
    """Request to analyze a project."""
    project_id: str
    analysis_types: list[str] = [
        "architecture", "bugs", "dead_code", "security",
        "tech_debt", "dependencies", "documentation"
    ]
    use_ai: bool = True

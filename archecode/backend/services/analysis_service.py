"""
Analysis orchestration service.
Coordinates multiple analyzers to produce comprehensive analysis results.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.analysis import (
    AnalysisResult, AnalysisRequest, AnalysisFinding,
    Severity, FindingCategory, CodeLocation, SecurityIssue,
    ModuleDependency, FunctionInfo, ClassInfo,
)
from models.project import Project, ProjectStatus
from services.project_service import project_service
from analyzers.code_analyzer import CodeAnalyzer
from analyzers.security_analyzer import SecurityAnalyzer
from analyzers.dependency_analyzer import DependencyAnalyzer
from analyzers.complexity_analyzer import ComplexityAnalyzer
from services.ai_service import AIService


# In-memory analysis store
_analyses: dict[str, AnalysisResult] = {}


class AnalysisService:
    """Orchestrates project analysis across multiple analyzers."""

    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.ai_service = AIService()

    async def analyze_project(self, request: AnalysisRequest) -> AnalysisResult:
        """Run a comprehensive analysis on a project."""
        project = await project_service.get_project(request.project_id)
        if not project:
            raise ValueError(f"Project {request.project_id} not found")
        if not project.upload_path:
            raise ValueError("Project has no upload path")

        analysis_id = str(uuid.uuid4())
        result = AnalysisResult(
            project_id=request.project_id,
            id=analysis_id,
        )

        root = Path(project.upload_path)
        all_findings: list[AnalysisFinding] = []
        all_security: list[SecurityIssue] = []
        all_deps: list[ModuleDependency] = []
        all_functions: list[FunctionInfo] = []
        all_classes: list[ClassInfo] = []

        # Collect source files
        source_files = self._collect_source_files(root)

        # Run analyzers based on requested types
        if "bugs" in request.analysis_types or "dead_code" in request.analysis_types:
            findings = self.code_analyzer.analyze(root, source_files)
            all_findings.extend(findings)

        if "security" in request.analysis_types:
            security_issues = self.security_analyzer.analyze(root, source_files)
            all_security.extend(security_issues)

        if "dependencies" in request.analysis_types:
            deps, funcs, classes = self.dependency_analyzer.analyze(root, source_files)
            all_deps.extend(deps)
            all_functions.extend(funcs)
            all_classes.extend(classes)

        if "tech_debt" in request.analysis_types or "bugs" in request.analysis_types:
            complexity_findings = self.complexity_analyzer.analyze(root, source_files)
            all_findings.extend(complexity_findings)

        # AI-powered analysis
        if request.use_ai and self.ai_service.is_configured():
            ai_summary = await self.ai_service.generate_project_summary(project)
            result.summary = ai_summary

            if "documentation" in request.analysis_types:
                readme = await self.ai_service.generate_readme(project)
                result.readme_content = readme

            if "architecture" in request.analysis_types:
                arch_desc = await self.ai_service.analyze_architecture(project)
                result.architecture_description = arch_desc

            # Generate refactoring suggestions
            if all_findings:
                suggestions = await self.ai_service.generate_refactoring_suggestions(
                    project, all_findings[:20]
                )
                result.refactoring_suggestions = suggestions
        else:
            result.summary = self._generate_basic_summary(project)

        # Populate result
        result.findings = all_findings
        result.security_issues = all_security
        result.dependencies = all_deps
        result.functions = all_functions
        result.classes = all_classes

        # Count findings by severity
        result.total_findings = len(all_findings) + len(all_security)
        for f in all_findings:
            if f.severity == Severity.CRITICAL:
                result.critical_count += 1
            elif f.severity == Severity.HIGH:
                result.high_count += 1
            elif f.severity == Severity.MEDIUM:
                result.medium_count += 1
            elif f.severity == Severity.LOW:
                result.low_count += 1
            else:
                result.info_count += 1

        for s in all_security:
            if s.severity == Severity.CRITICAL:
                result.critical_count += 1
            elif s.severity == Severity.HIGH:
                result.high_count += 1

        # Calculate health score
        result.overall_health_score = self._calculate_health_score(result)

        # Store result
        _analyses[analysis_id] = result
        return result

    async def get_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Get an analysis result by ID."""
        return _analyses.get(analysis_id)

    async def get_project_analyses(self, project_id: str) -> list[AnalysisResult]:
        """Get all analyses for a project."""
        return [a for a in _analyses.values() if a.project_id == project_id]

    def _collect_source_files(self, root: Path) -> list[Path]:
        """Collect all source files worth analyzing."""
        from services.project_service import SKIP_DIRS, LANGUAGE_MAP

        files = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in LANGUAGE_MAP:
                continue
            # Skip files in ignored directories
            skip = False
            for part in file_path.parts:
                if part in SKIP_DIRS:
                    skip = True
                    break
            if skip:
                continue
            # Skip large files (> 500KB)
            try:
                if file_path.stat().st_size > 500 * 1024:
                    continue
            except OSError:
                continue
            files.append(file_path)
        return files

    def _generate_basic_summary(self, project: Project) -> str:
        """Generate a basic summary without AI."""
        meta = project.metadata
        if not meta:
            return f"Project '{project.name}' has been analyzed."

        lines = [
            f"# {project.name}",
            "",
            f"Type: {meta.project_type.value.replace('_', ' ').title()}",
            f"Architecture: {meta.architecture_pattern.value.replace('_', ' ').title()}",
            f"Total Files: {meta.total_files}",
            f"Total Lines: {meta.total_lines:,}",
            "",
            "## Languages",
        ]
        for lang, count in sorted(meta.languages.items(), key=lambda x: -x[1]):
            lines.append(f"- {lang}: {count:,} lines")

        if meta.tech_stack:
            lines.extend(["", "## Tech Stack"])
            for tech in meta.tech_stack:
                lines.append(f"- {tech.name}")

        return "\n".join(lines)

    def _calculate_health_score(self, result: AnalysisResult) -> float:
        """Calculate an overall project health score (0-100)."""
        score = 100.0

        # Deduct for findings
        score -= result.critical_count * 10
        score -= result.high_count * 5
        score -= result.medium_count * 2
        score -= result.low_count * 0.5
        score -= result.info_count * 0.1

        return max(0.0, min(100.0, score))


# Singleton
analysis_service = AnalysisService()

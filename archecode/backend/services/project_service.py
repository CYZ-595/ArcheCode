"""
Project management service.
Handles project uploads, extraction, file tree building, and tech stack detection.
"""

import os
import zipfile
import shutil
import uuid
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

import git
import chardet
from binaryornot.check import is_binary

from models.project import (
    Project, ProjectStatus, ProjectType, ProjectMetadata,
    FileNode, TechStackItem, ArchitecturePattern,
)
from core.config import settings


# In-memory project store (replace with database in production)
_projects: dict[str, Project] = {}

# Tech stack detection patterns
TECH_PATTERNS: dict[str, dict[str, list[str]]] = {
    "package.json": {
        "react": ["react"],
        "next.js": ["next"],
        "vue.js": ["vue"],
        "angular": ["@angular/core"],
        "express": ["express"],
        "fastify": ["fastify"],
        "typescript": ["typescript"],
        "tailwindcss": ["tailwindcss"],
        "prisma": ["prisma"],
        "mongodb": ["mongodb", "mongoose"],
        "postgresql": ["pg", "postgres"],
        "redis": ["redis"],
        "jest": ["jest"],
        "cypress": ["cypress"],
        "eslint": ["eslint"],
        "webpack": ["webpack"],
        "vite": ["vite"],
    },
    "requirements.txt": {
        "fastapi": ["fastapi"],
        "django": ["django"],
        "flask": ["flask"],
        "celery": ["celery"],
        "sqlalchemy": ["sqlalchemy"],
        "pydantic": ["pydantic"],
        "pytest": ["pytest"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "tensorflow": ["tensorflow"],
        "pytorch": ["torch"],
        "scikit-learn": ["scikit-learn"],
        "openai": ["openai"],
        "redis": ["redis"],
        "celery": ["celery"],
    },
    "pom.xml": {
        "spring-boot": ["spring-boot"],
        "maven": ["maven"],
    },
    "build.gradle": {
        "spring-boot": ["spring-boot"],
        "gradle": ["gradle"],
    },
    "go.mod": {
        "gin": ["gin-gonic"],
        "echo": ["labstack/echo"],
        "fiber": ["gofiber"],
    },
    "Cargo.toml": {
        "actix": ["actix-web"],
        "tokio": ["tokio"],
        "serde": ["serde"],
    },
}

# Framework detection by file patterns
FRAMEWORK_INDICATORS: dict[str, list[str]] = {
    "next.js": ["next.config.js", "next.config.mjs", "next.config.ts", "app/layout.tsx", "pages/_app.tsx"],
    "react": ["src/App.tsx", "src/App.jsx", "src/index.tsx"],
    "vue.js": ["vue.config.js", "src/App.vue"],
    "angular": ["angular.json", "src/app/app.module.ts"],
    "django": ["manage.py", "settings.py"],
    "flask": ["app.py", "wsgi.py"],
    "fastapi": ["main.py"],
    "spring-boot": ["src/main/java"],
    "express": ["app.js", "server.js"],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "kubernetes": ["k8s/", "kubernetes/", "deployment.yaml"],
    "terraform": ["main.tf", "variables.tf"],
    "ci/cd": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/"],
}

# Language extension mapping
LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (TSX)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Bash",
    ".graphql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".toml": "TOML",
}

# Directories to skip during analysis
SKIP_DIRS: set[str] = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".env", "dist", "build", ".next", ".nuxt", "coverage",
    ".tox", ".mypy_cache", ".pytest_cache", ".cache",
    "vendor", "target", "bin", "obj", ".gradle", ".idea", ".vscode",
    "bower_components", ".sass-cache", ".parcel-cache",
}


class ProjectService:
    """Handles project lifecycle: upload, extract, analyze metadata."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def upload_zip(self, file_content: bytes, filename: str) -> Project:
        """Upload and extract a zip file."""
        project_id = str(uuid.uuid4())
        project_name = Path(filename).stem
        project_dir = self.upload_dir / project_id

        project = Project(
            id=project_id,
            name=project_name,
            status=ProjectStatus.EXTRACTING,
            source_type="zip",
        )
        _projects[project_id] = project

        # Save zip file
        zip_path = self.temp_dir / f"{project_id}.zip"
        zip_path.write_bytes(file_content)

        try:
            # Extract zip
            project_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(project_dir)

            # Handle nested directories (e.g., GitHub zip has a top-level folder)
            contents = list(project_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                nested = contents[0]
                for item in nested.iterdir():
                    shutil.move(str(item), str(project_dir))
                nested.rmdir()

            project.upload_path = str(project_dir)
            project.status = ProjectStatus.ANALYZING
            _projects[project_id] = project

            # Build metadata
            metadata = await self._build_metadata(project_dir, project_name)
            file_tree = self._build_file_tree(project_dir, project_dir)

            project.metadata = metadata
            project.file_tree = file_tree
            project.status = ProjectStatus.COMPLETED
            project.updated_at = datetime.utcnow()
            _projects[project_id] = project

        except Exception as e:
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            _projects[project_id] = project
        finally:
            if zip_path.exists():
                zip_path.unlink()

        return project

    async def import_github(self, repo_url: str) -> Project:
        """Clone a GitHub repository."""
        project_id = str(uuid.uuid4())
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        project_dir = self.upload_dir / project_id

        project = Project(
            id=project_id,
            name=repo_name,
            status=ProjectStatus.EXTRACTING,
            source_type="github",
            source_url=repo_url,
        )
        _projects[project_id] = project

        try:
            # Clone repository
            clone_kwargs = {"depth": 1, "single_branch": True}
            if settings.GITHUB_TOKEN:
                authed_url = repo_url.replace(
                    "https://", f"https://{settings.GITHUB_TOKEN}@"
                )
            else:
                authed_url = repo_url

            await asyncio.to_thread(
                git.Repo.clone_from, authed_url, str(project_dir), **clone_kwargs
            )

            # Remove .git directory to save space
            git_dir = project_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

            project.upload_path = str(project_dir)
            project.status = ProjectStatus.ANALYZING
            _projects[project_id] = project

            # Build metadata
            metadata = await self._build_metadata(project_dir, repo_name)
            file_tree = self._build_file_tree(project_dir, project_dir)

            project.metadata = metadata
            project.file_tree = file_tree
            project.status = ProjectStatus.COMPLETED
            project.updated_at = datetime.utcnow()
            _projects[project_id] = project

        except Exception as e:
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            _projects[project_id] = project

        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return _projects.get(project_id)

    async def list_projects(self) -> list[Project]:
        """List all projects."""
        return list(_projects.values())

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and its files."""
        project = _projects.get(project_id)
        if not project:
            return False

        if project.upload_path and Path(project.upload_path).exists():
            shutil.rmtree(project.upload_path)

        del _projects[project_id]
        return True

    async def get_project_files(self, project_id: str) -> list[str]:
        """Get list of all source files in the project."""
        project = _projects.get(project_id)
        if not project or not project.upload_path:
            return []

        files = []
        root = Path(project.upload_path)
        for file_path in root.rglob("*"):
            if file_path.is_file() and not self._should_skip(file_path):
                rel_path = str(file_path.relative_to(root))
                files.append(rel_path)
        return files

    async def read_project_file(self, project_id: str, file_path: str) -> Optional[str]:
        """Read a specific file from the project."""
        project = _projects.get(project_id)
        if not project or not project.upload_path:
            return None

        full_path = Path(project.upload_path) / file_path
        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            if is_binary(str(full_path)):
                return "[Binary file]"

            raw = full_path.read_bytes()
            detected = chardet.detect(raw)
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            return raw.decode(encoding, errors="replace")
        except Exception:
            return None

    async def _build_metadata(self, root: Path, name: str) -> ProjectMetadata:
        """Build project metadata by analyzing the file tree."""
        total_files = 0
        total_lines = 0
        languages: dict[str, int] = {}
        has_tests = False
        has_docs = False
        has_ci = False
        has_docker = False
        entry_points: list[str] = []
        tech_stack: list[TechStackItem] = []

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if self._should_skip(file_path):
                continue

            total_files += 1
            ext = file_path.suffix.lower()
            rel_path = str(file_path.relative_to(root))

            # Count lines
            line_count = self._count_lines(file_path)
            total_lines += line_count

            # Track languages
            lang = LANGUAGE_MAP.get(ext)
            if lang:
                languages[lang] = languages.get(lang, 0) + line_count

            # Check for tests
            if any(t in rel_path.lower() for t in ["test", "spec", "__tests__"]):
                has_tests = True

            # Check for docs
            if any(d in rel_path.lower() for d in ["docs/", "doc/", "readme"]):
                has_docs = True

            # Check for CI
            if any(c in rel_path for c in [".github/workflows", ".gitlab-ci", "Jenkinsfile", ".circleci"]):
                has_ci = True

            # Check for Docker
            if file_path.name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                has_docker = True

            # Detect entry points
            if file_path.name in ("main.py", "app.py", "server.py", "index.js", "index.ts", "main.go", "Main.java"):
                entry_points.append(rel_path)

            # Detect tech stack from config files
            if file_path.name in TECH_PATTERNS:
                tech_stack.extend(self._detect_tech_from_file(file_path, file_path.name))

        # Detect frameworks from file patterns
        for framework, indicators in FRAMEWORK_INDICATORS.items():
            for indicator in indicators:
                if (root / indicator).exists() or any(
                    str(f.relative_to(root)).startswith(indicator)
                    for f in root.rglob("*")
                    if f.is_file()
                ):
                    tech_stack.append(TechStackItem(
                        name=framework,
                        category="framework",
                        confidence=0.9,
                    ))
                    break

        # Deduplicate tech stack
        seen = set()
        unique_stack = []
        for item in tech_stack:
            if item.name not in seen:
                seen.add(item.name)
                unique_stack.append(item)

        # Determine project type
        project_type = self._determine_project_type(unique_stack, entry_points, root)

        # Determine architecture pattern
        arch_pattern = self._determine_architecture(root)

        return ProjectMetadata(
            name=name,
            project_type=project_type,
            architecture_pattern=arch_pattern,
            tech_stack=unique_stack,
            entry_points=entry_points,
            total_files=total_files,
            total_lines=total_lines,
            languages=languages,
            has_tests=has_tests,
            has_docs=has_docs,
            has_ci=has_ci,
            has_docker=has_docker,
        )

    def _build_file_tree(self, root: Path, current: Path, max_depth: int = 10) -> FileNode:
        """Recursively build a file tree."""
        if max_depth <= 0:
            return FileNode(
                name=current.name,
                path=str(current.relative_to(root)),
                is_directory=True,
            )

        if current.is_file():
            ext = current.suffix.lower()
            return FileNode(
                name=current.name,
                path=str(current.relative_to(root)),
                is_directory=False,
                size=current.stat().st_size,
                language=LANGUAGE_MAP.get(ext),
                line_count=self._count_lines(current),
            )

        children = []
        try:
            sorted_items = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for item in sorted_items:
                if item.name.startswith(".") and item.name not in (".env.example",):
                    continue
                if item.name in SKIP_DIRS:
                    continue
                child = self._build_file_tree(root, item, max_depth - 1)
                children.append(child)
        except PermissionError:
            pass

        return FileNode(
            name=current.name if current != root else "/",
            path=str(current.relative_to(root)) if current != root else "/",
            is_directory=True,
            children=children,
        )

    def _detect_tech_from_file(self, file_path: Path, config_name: str) -> list[TechStackItem]:
        """Detect technologies from a config file's contents."""
        items = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            patterns = TECH_PATTERNS.get(config_name, {})
            for tech_name, keywords in patterns.items():
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        items.append(TechStackItem(
                            name=tech_name,
                            category="dependency",
                            confidence=0.85,
                        ))
                        break
        except Exception:
            pass
        return items

    def _determine_project_type(
        self, tech_stack: list[TechStackItem], entry_points: list[str], root: Path
    ) -> ProjectType:
        """Determine the project type based on detected tech stack."""
        tech_names = {t.name.lower() for t in tech_stack}

        if tech_names & {"fastapi", "flask", "django", "express", "spring-boot"}:
            if tech_names & {"react", "next.js", "vue.js", "angular"}:
                return ProjectType.WEB_APP
            return ProjectType.API_SERVICE

        if tech_names & {"react", "next.js", "vue.js", "angular"}:
            return ProjectType.WEB_APP

        # Check for CLI patterns
        for ep in entry_points:
            if "cli" in ep.lower() or "command" in ep.lower():
                return ProjectType.CLI_TOOL

        # Check if it has setup.py / pyproject.toml (library)
        if (root / "setup.py").exists() or (root / "pyproject.toml").exists():
            return ProjectType.LIBRARY

        return ProjectType.UNKNOWN

    def _determine_architecture(self, root: Path) -> ArchitecturePattern:
        """Determine architecture pattern from directory structure."""
        dirs = set()
        for item in root.iterdir():
            if item.is_dir():
                dirs.add(item.name.lower())

        # MVC pattern
        if {"models", "views", "controllers"} <= dirs or {"model", "view", "controller"} <= dirs:
            return ArchitecturePattern.MVC

        # Clean architecture
        if {"domain", "infrastructure", "application"} <= dirs:
            return ArchitecturePattern.CLEAN_ARCHITECTURE
        if {"entities", "use_cases", "adapters", "frameworks"} <= dirs:
            return ArchitecturePattern.CLEAN_ARCHITECTURE

        # Layered
        if {"services", "repositories", "controllers"} <= dirs:
            return ArchitecturePattern.LAYERED

        # Microservices (check for multiple service directories)
        service_dirs = [d for d in dirs if "service" in d.lower()]
        if len(service_dirs) >= 2:
            return ArchitecturePattern.MICROSERVICES

        return ArchitecturePattern.UNKNOWN

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file, returning 0 for binary files."""
        try:
            if is_binary(str(file_path)):
                return 0
            content = file_path.read_bytes()
            return content.count(b"\n") + 1
        except Exception:
            return 0

    def _should_skip(self, file_path: Path) -> bool:
        """Check if a file should be skipped during analysis."""
        parts = file_path.parts
        for part in parts:
            if part in SKIP_DIRS:
                return True
        if file_path.suffix.lower() in {".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe", ".bin"}:
            return True
        return False


# Singleton instance
project_service = ProjectService()

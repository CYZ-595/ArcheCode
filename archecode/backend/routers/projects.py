"""
Project management API endpoints.
Handles project upload, GitHub import, listing, and file access.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from models.project import Project, ProjectUploadResponse, ProjectSummary
from services.project_service import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


class GitHubImportRequest(BaseModel):
    """Request to import a GitHub repository."""
    url: str


@router.post("/upload", response_model=ProjectUploadResponse)
async def upload_project(file: UploadFile = File(...)):
    """Upload a project as a zip file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    content = await file.read()
    max_size = 50 * 1024 * 1024  # 50MB
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    try:
        project = await project_service.upload_zip(content, file.filename)
        return ProjectUploadResponse(
            project_id=project.id,
            status=project.status,
            message="Project uploaded and analysis started.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-github", response_model=ProjectUploadResponse)
async def import_github_repo(request: GitHubImportRequest):
    """Import a project from a GitHub repository URL."""
    url = request.url.strip()

    if not url.startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Must start with https://github.com/",
        )

    try:
        project = await project_service.import_github(url)
        return ProjectUploadResponse(
            project_id=project.id,
            status=project.status,
            message="Repository imported and analysis started.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ProjectSummary])
async def list_projects():
    """List all projects."""
    projects = await project_service.list_projects()
    return [
        ProjectSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            status=p.status,
            project_type=p.metadata.project_type if p.metadata else "unknown",
            total_files=p.metadata.total_files if p.metadata else 0,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a project by ID with full details."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/files")
async def list_project_files(project_id: str):
    """List all source files in a project."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = await project_service.get_project_files(project_id)
    return {"files": files}


@router.get("/{project_id}/files/{file_path:path}")
async def read_project_file(project_id: str, file_path: str):
    """Read a specific file from the project."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await project_service.read_project_file(project_id, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    return {"file_path": file_path, "content": content}


@router.get("/{project_id}/tree")
async def get_project_tree(project_id: str):
    """Get the project file tree structure."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.file_tree:
        raise HTTPException(status_code=404, detail="File tree not available")

    return project.file_tree

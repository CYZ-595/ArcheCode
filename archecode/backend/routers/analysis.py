"""
Analysis API endpoints.
Handles triggering analysis, retrieving results, and generating visualizations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.analysis import AnalysisRequest, AnalysisResult
from services.analysis_service import analysis_service
from services.project_service import project_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/start", response_model=AnalysisResult)
async def start_analysis(request: AnalysisRequest):
    """Start a comprehensive analysis of a project."""
    project = await project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = await analysis_service.analyze_project(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str):
    """Get an analysis result by ID."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/project/{project_id}", response_model=list[AnalysisResult])
async def get_project_analyses(project_id: str):
    """Get all analyses for a project."""
    results = await analysis_service.get_project_analyses(project_id)
    return results


@router.get("/{analysis_id}/findings")
async def get_findings(
    analysis_id: str,
    category: Optional[str] = None,
    severity: Optional[str] = None,
):
    """Get analysis findings with optional filters."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    findings = result.findings

    if category:
        findings = [f for f in findings if f.category.value == category]
    if severity:
        findings = [f for f in findings if f.severity.value == severity]

    return {"findings": findings, "total": len(findings)}


@router.get("/{analysis_id}/security")
async def get_security_issues(analysis_id: str):
    """Get security issues from analysis."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {"issues": result.security_issues, "total": len(result.security_issues)}


@router.get("/{analysis_id}/dependencies")
async def get_dependencies(analysis_id: str):
    """Get module dependencies from analysis."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "dependencies": result.dependencies,
        "functions": result.functions,
        "classes": result.classes,
    }


@router.get("/{analysis_id}/graph/dependencies")
async def get_dependency_graph(analysis_id: str):
    """Get dependency graph data formatted for React Flow visualization."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    nodes = []
    edges = []
    node_ids = set()

    for dep in result.dependencies:
        # Add source node
        source_id = dep.source.replace("/", "_").replace(".", "_")
        if source_id not in node_ids:
            node_ids.add(source_id)
            nodes.append({
                "id": source_id,
                "label": dep.source.split("/")[-1],
                "type": "file",
                "data": {"fullPath": dep.source},
            })

        # Add target node
        target_id = dep.target.replace("/", "_").replace(".", "_")
        if target_id not in node_ids:
            node_ids.add(target_id)
            is_external = not dep.target.startswith(".")
            nodes.append({
                "id": target_id,
                "label": dep.target.split("/")[-1] if "/" in dep.target else dep.target,
                "type": "external" if is_external else "file",
                "data": {"fullPath": dep.target, "isExternal": is_external},
            })

        edges.append({
            "id": f"{source_id}-{target_id}",
            "source": source_id,
            "target": target_id,
            "label": dep.dependency_type,
            "animated": dep.weight > 1.5,
        })

    return {"nodes": nodes, "edges": edges}


@router.get("/{analysis_id}/graph/functions")
async def get_function_graph(analysis_id: str):
    """Get function relationship graph data for React Flow."""
    result = await analysis_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    nodes = []
    edges = []
    node_ids = set()

    for func in result.functions[:100]:  # Limit for performance
        func_id = f"{func.file_path}_{func.name}".replace("/", "_").replace(".", "_")
        if func_id not in node_ids:
            node_ids.add(func_id)
            nodes.append({
                "id": func_id,
                "label": func.name,
                "type": "function",
                "data": {
                    "file": func.file_path,
                    "line": func.line_start,
                    "params": func.parameters,
                    "complexity": func.complexity,
                },
            })

        # Add caller edges
        for caller in func.callers:
            caller_id = f"{func.file_path}_{caller}".replace("/", "_").replace(".", "_")
            edges.append({
                "id": f"{caller_id}-{func_id}",
                "source": caller_id,
                "target": func_id,
            })

    return {"nodes": nodes, "edges": edges}

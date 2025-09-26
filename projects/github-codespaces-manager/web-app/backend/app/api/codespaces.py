"""
Codespaces API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.github_manager import WebGitHubManager
from app.core.websockets import WebSocketManager

router = APIRouter()

# Initialize managers
github_manager = WebGitHubManager()
websocket_manager = WebSocketManager()


class CreateCodespaceRequest(BaseModel):
    repository: str
    branch: Optional[str] = "main"
    machine_type: Optional[str] = "basicLinux32gb"
    region: Optional[str] = "EuropeWest"


class CodespaceActionRequest(BaseModel):
    codespace_name: str


@router.get("/")
async def list_codespaces():
    """Get all codespaces"""
    try:
        result = await github_manager.get_codespaces()

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "data": result["codespaces"],
            "count": result["count"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{codespace_name}")
async def get_codespace(codespace_name: str):
    """Get specific codespace details"""
    try:
        result = await github_manager.get_codespaces()

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Find specific codespace
        codespace = None
        for cs in result["codespaces"]:
            if cs["name"] == codespace_name:
                codespace = cs
                break

        if not codespace:
            raise HTTPException(status_code=404, detail="Codespace not found")

        return {
            "success": True,
            "data": codespace
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_codespace(request: CreateCodespaceRequest, background_tasks: BackgroundTasks):
    """Create a new codespace"""
    try:
        # Send WebSocket notification
        await websocket_manager.send_operation_update(
            operation_id=f"create_{request.repository}",
            status="started",
            message=f"Creating codespace for {request.repository}..."
        )

        result = await github_manager.create_codespace(
            repo=request.repository,
            branch=request.branch,
            machine=request.machine_type,
            region=request.region
        )

        if result["success"]:
            await websocket_manager.send_operation_update(
                operation_id=f"create_{request.repository}",
                status="completed",
                message="Codespace created successfully!"
            )

            return {
                "success": True,
                "message": result["message"],
                "data": {
                    "repository": result["repository"],
                    "branch": result["branch"],
                    "machine_type": result["machine_type"],
                    "region": result["region"]
                }
            }
        else:
            await websocket_manager.send_operation_update(
                operation_id=f"create_{request.repository}",
                status="failed",
                message=f"Failed to create codespace: {result.get('error', 'Unknown error')}"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create codespace"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error creating codespace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{codespace_name}/start")
async def start_codespace(codespace_name: str):
    """Start a codespace"""
    try:
        await websocket_manager.send_codespace_update(
            codespace_name=codespace_name,
            action="start",
            status="starting"
        )

        result = await github_manager.start_codespace(codespace_name)

        if result["success"]:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="start",
                status="completed"
            )

            return {
                "success": True,
                "message": result["message"],
                "codespace_name": codespace_name
            }
        else:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="start",
                status="failed"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start codespace"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error starting codespace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{codespace_name}/stop")
async def stop_codespace(codespace_name: str):
    """Stop a codespace"""
    try:
        await websocket_manager.send_codespace_update(
            codespace_name=codespace_name,
            action="stop",
            status="stopping"
        )

        result = await github_manager.stop_codespace(codespace_name)

        if result["success"]:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="stop",
                status="completed"
            )

            return {
                "success": True,
                "message": result["message"],
                "codespace_name": codespace_name
            }
        else:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="stop",
                status="failed"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to stop codespace"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error stopping codespace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{codespace_name}")
async def delete_codespace(codespace_name: str):
    """Delete a codespace"""
    try:
        await websocket_manager.send_codespace_update(
            codespace_name=codespace_name,
            action="delete",
            status="deleting"
        )

        result = await github_manager.delete_codespace(codespace_name)

        if result["success"]:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="delete",
                status="completed"
            )

            return {
                "success": True,
                "message": result["message"],
                "codespace_name": codespace_name
            }
        else:
            await websocket_manager.send_codespace_update(
                codespace_name=codespace_name,
                action="delete",
                status="failed"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete codespace"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error deleting codespace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/list")
async def list_repositories(limit: int = 20):
    """Get user's repositories"""
    try:
        result = await github_manager.get_repositories(limit=limit)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "data": result["repositories"],
            "count": result["count"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
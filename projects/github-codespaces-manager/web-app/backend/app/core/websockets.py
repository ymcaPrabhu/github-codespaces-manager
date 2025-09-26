"""
WebSocket connection manager for real-time updates
"""

import json
import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": datetime.now(),
            "user_id": None,  # Can be set later with authentication
        }

        # Send welcome message
        await self.send_personal_message(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "Connected to GitHub Codespaces Manager",
            "timestamp": datetime.now().isoformat()
        }), websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_text(message)
        except:
            # Connection might be closed, remove it
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        message_str = json.dumps({
            **message,
            "timestamp": datetime.now().isoformat()
        })

        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_operation_update(self, operation_id: str, status: str,
                                  progress: int = None, message: str = None,
                                  data: Dict[str, Any] = None):
        """Send operation status update"""
        update = {
            "type": "operation_update",
            "operation_id": operation_id,
            "status": status,
        }

        if progress is not None:
            update["progress"] = progress
        if message:
            update["message"] = message
        if data:
            update["data"] = data

        await self.broadcast(update)

    async def send_codespace_update(self, codespace_name: str, action: str,
                                  status: str, data: Dict[str, Any] = None):
        """Send codespace status update"""
        update = {
            "type": "codespace_update",
            "codespace_name": codespace_name,
            "action": action,
            "status": status,
        }

        if data:
            update["data"] = data

        await self.broadcast(update)

    async def send_metrics_update(self, metrics: Dict[str, Any]):
        """Send metrics update"""
        update = {
            "type": "metrics_update",
            "metrics": metrics
        }
        await self.broadcast(update)

    async def send_error(self, error: str, details: str = None):
        """Send error notification"""
        error_msg = {
            "type": "error",
            "error": error,
        }

        if details:
            error_msg["details"] = details

        await self.broadcast(error_msg)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections"""
        return [
            {
                "connected_at": data["connected_at"].isoformat(),
                "user_id": data["user_id"],
            }
            for data in self.connection_data.values()
        ]
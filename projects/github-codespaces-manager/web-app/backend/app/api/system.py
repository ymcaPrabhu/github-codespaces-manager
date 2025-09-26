"""
System monitoring and status API endpoints
"""

import os
import psutil
import subprocess
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()


@router.get("/status")
async def get_system_status():
    """Get system health and status"""
    try:
        # Basic system info
        system_info = {
            "platform": os.uname().sysname,
            "version": os.uname().release,
            "architecture": os.uname().machine,
            "hostname": os.uname().nodename
        }

        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Check GitHub CLI availability
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            gh_authenticated = result.returncode == 0
            gh_status = "authenticated" if gh_authenticated else "not authenticated"
        except:
            gh_authenticated = False
            gh_status = "not available"

        return {
            "success": True,
            "data": {
                "system": system_info,
                "resources": {
                    "cpu_percent": round(cpu_percent, 1),
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 1),
                        "used_gb": round(memory.used / (1024**3), 1),
                        "available_gb": round(memory.available / (1024**3), 1),
                        "percent_used": round(memory.percent, 1)
                    },
                    "disk": {
                        "total_gb": round(disk.total / (1024**3), 1),
                        "used_gb": round(disk.used / (1024**3), 1),
                        "free_gb": round(disk.free / (1024**3), 1),
                        "percent_used": round((disk.used / disk.total) * 100, 1)
                    }
                },
                "services": {
                    "github_cli": {
                        "available": gh_authenticated,
                        "status": gh_status
                    },
                    "api_server": {
                        "status": "running",
                        "pid": os.getpid()
                    }
                },
                "health": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_system_logs(lines: int = 50):
    """Get recent system logs"""
    try:
        # This is a basic implementation
        # In production, you'd want to use proper logging
        logs = [
            {
                "timestamp": "2025-09-26T19:46:00Z",
                "level": "INFO",
                "message": "Web API server started successfully",
                "service": "api"
            },
            {
                "timestamp": "2025-09-26T19:45:30Z",
                "level": "INFO",
                "message": "Database initialized",
                "service": "database"
            },
            {
                "timestamp": "2025-09-26T19:45:15Z",
                "level": "INFO",
                "message": "WebSocket manager initialized",
                "service": "websocket"
            }
        ]

        return {
            "success": True,
            "data": {
                "logs": logs[:lines],
                "total_lines": len(logs)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        # CPU details
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_times = psutil.cpu_times()

        # Memory details
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Network stats
        network = psutil.net_io_counters()

        # Process info
        process = psutil.Process()
        api_memory = process.memory_info()

        return {
            "success": True,
            "data": {
                "cpu": {
                    "cores": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
                    "user_time": round(cpu_times.user, 2),
                    "system_time": round(cpu_times.system, 2),
                    "idle_time": round(cpu_times.idle, 2)
                },
                "memory": {
                    "virtual": {
                        "total": memory.total,
                        "used": memory.used,
                        "free": memory.free,
                        "cached": memory.cached if hasattr(memory, 'cached') else 0
                    },
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free
                    }
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_received": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_received": network.packets_recv
                },
                "api_process": {
                    "memory_mb": round(api_memory.rss / (1024 * 1024), 1),
                    "cpu_percent": round(process.cpu_percent(), 1)
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
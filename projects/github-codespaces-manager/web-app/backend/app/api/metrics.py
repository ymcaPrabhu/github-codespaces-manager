"""
Metrics and monitoring API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.github_manager import WebGitHubManager

router = APIRouter()

# Initialize manager
github_manager = WebGitHubManager()


@router.get("/overview")
async def get_metrics_overview():
    """Get overview metrics for dashboard"""
    try:
        # Get codespaces data
        codespaces_result = await github_manager.get_codespaces()

        if "error" in codespaces_result:
            raise HTTPException(status_code=500, detail=codespaces_result["error"])

        codespaces = codespaces_result["codespaces"]

        # Calculate metrics
        total_codespaces = len(codespaces)
        running_codespaces = len([cs for cs in codespaces if cs["state"] == "Available"])
        shutdown_codespaces = len([cs for cs in codespaces if cs["state"] == "Shutdown"])

        # Calculate costs
        total_hourly_cost = sum(cs.get("cost_estimate", 0.18) for cs in codespaces)
        running_hourly_cost = sum(
            cs.get("cost_estimate", 0.18) for cs in codespaces
            if cs["state"] == "Available"
        )

        # Storage estimates (simplified)
        estimated_storage_gb = total_codespaces * 1.5  # Rough estimate

        # Group by machine type
        machine_types = {}
        for cs in codespaces:
            machine_type = cs.get("machine_type", "Unknown")
            if machine_type not in machine_types:
                machine_types[machine_type] = {"count": 0, "cost": 0}
            machine_types[machine_type]["count"] += 1
            machine_types[machine_type]["cost"] += cs.get("cost_estimate", 0.18)

        return {
            "success": True,
            "data": {
                "overview": {
                    "total_codespaces": total_codespaces,
                    "running_codespaces": running_codespaces,
                    "shutdown_codespaces": shutdown_codespaces,
                    "total_hourly_cost": round(total_hourly_cost, 2),
                    "running_hourly_cost": round(running_hourly_cost, 2),
                    "estimated_storage_gb": round(estimated_storage_gb, 1)
                },
                "machine_types": machine_types,
                "cost_breakdown": {
                    "running_cost_per_hour": round(running_hourly_cost, 2),
                    "daily_cost_estimate": round(running_hourly_cost * 24, 2),
                    "monthly_cost_estimate": round(running_hourly_cost * 24 * 30, 2)
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs")
async def get_cost_analysis():
    """Get detailed cost analysis"""
    try:
        codespaces_result = await github_manager.get_codespaces()

        if "error" in codespaces_result:
            raise HTTPException(status_code=500, detail=codespaces_result["error"])

        codespaces = codespaces_result["codespaces"]

        # Cost analysis per codespace
        cost_analysis = []
        for cs in codespaces:
            hourly_cost = cs.get("cost_estimate", 0.18)

            # Estimate usage based on state
            if cs["state"] == "Available":
                daily_estimate = hourly_cost * 8  # Assume 8 hours/day usage
            else:
                daily_estimate = 0  # Shutdown codespaces don't cost when stopped

            cost_analysis.append({
                "name": cs["name"],
                "repository": cs["repository"],
                "state": cs["state"],
                "machine_type": cs["machine_type"],
                "hourly_cost": hourly_cost,
                "daily_estimate": round(daily_estimate, 2),
                "monthly_estimate": round(daily_estimate * 30, 2)
            })

        # Machine type pricing
        machine_pricing = {
            "basicLinux32gb": {"hourly": 0.18, "cores": 2, "ram_gb": 4, "storage_gb": 32},
            "standardLinux32gb": {"hourly": 0.36, "cores": 4, "ram_gb": 8, "storage_gb": 32},
            "premiumLinux64gb": {"hourly": 0.72, "cores": 8, "ram_gb": 16, "storage_gb": 64},
            "largeLinux128gb": {"hourly": 1.44, "cores": 16, "ram_gb": 32, "storage_gb": 128}
        }

        return {
            "success": True,
            "data": {
                "codespace_costs": cost_analysis,
                "machine_pricing": machine_pricing,
                "cost_optimization_tips": [
                    "Stop codespaces when not in use to avoid charges",
                    "Use smaller machine types for lighter workloads",
                    "Consider deleting unused codespaces",
                    "Monitor usage patterns to optimize machine selection"
                ]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def get_usage_metrics():
    """Get usage metrics and patterns"""
    try:
        codespaces_result = await github_manager.get_codespaces()

        if "error" in codespaces_result:
            raise HTTPException(status_code=500, detail=codespaces_result["error"])

        codespaces = codespaces_result["codespaces"]

        # Analyze usage patterns
        repositories = {}
        states = {"Available": 0, "Shutdown": 0, "Unknown": 0}

        for cs in codespaces:
            # Repository usage
            repo = cs["repository"]
            if repo not in repositories:
                repositories[repo] = {"count": 0, "states": {"Available": 0, "Shutdown": 0}}
            repositories[repo]["count"] += 1

            # State distribution
            state = cs["state"]
            if state in states:
                states[state] += 1
                repositories[repo]["states"][state] = repositories[repo]["states"].get(state, 0) + 1
            else:
                states["Unknown"] += 1

        # Most active repositories
        active_repos = sorted(
            repositories.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]

        return {
            "success": True,
            "data": {
                "state_distribution": states,
                "repository_usage": dict(repositories),
                "most_active_repositories": [
                    {"repository": repo, "codespace_count": data["count"]}
                    for repo, data in active_repos
                ],
                "total_repositories": len(repositories),
                "avg_codespaces_per_repo": round(len(codespaces) / max(len(repositories), 1), 1)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced")
async def get_advanced_metrics():
    """Get advanced metrics using the existing advanced module"""
    try:
        metrics = await github_manager.get_metrics()

        if "error" in metrics:
            return {
                "success": False,
                "error": metrics["error"],
                "data": {
                    "message": "Advanced metrics temporarily unavailable",
                    "basic_metrics_available": True
                }
            }

        return {
            "success": True,
            "data": metrics
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "message": "Advanced metrics temporarily unavailable",
                "basic_metrics_available": True
            }
        }
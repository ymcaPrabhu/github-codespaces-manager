"""
GitHub CLI integration for web API
Wraps the existing GitHub CLI functionality for web use
"""

import os
import sys
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add the parent CLI directory to import existing modules
CLI_DIR = os.path.join(os.path.dirname(__file__), '../../../../')
sys.path.append(CLI_DIR)

try:
    # Import existing GitHub manager
    from codespaces_advanced import CodespacesAdvanced
    HAS_ADVANCED = True
except ImportError:
    HAS_ADVANCED = False


class WebGitHubManager:
    """Web-friendly GitHub CLI manager"""

    def __init__(self):
        self.cli_path = "gh"
        self.advanced = None
        if HAS_ADVANCED:
            self.advanced = CodespacesAdvanced(self)

    async def run_gh_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run GitHub CLI command asynchronously"""
        try:
            full_cmd = [self.cli_path] + cmd

            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            output = stdout.decode('utf-8') if success else stderr.decode('utf-8')

            return success, output.strip()

        except Exception as e:
            return False, f"Command execution error: {str(e)}"

    async def get_codespaces(self) -> Dict[str, Any]:
        """Get list of all codespaces"""
        try:
            success, output = await self.run_gh_command([
                'codespace', 'list', '--json',
                'name,repository,state,displayName,gitStatus,machineName,lastUsedAt,createdAt,owner'
            ])

            if not success:
                return {"error": output, "codespaces": []}

            codespaces_data = json.loads(output) if output.strip() else []

            # Process each codespace
            processed_codespaces = []
            for cs in codespaces_data:
                processed_cs = self._process_codespace_data(cs)
                processed_codespaces.append(processed_cs)

            return {
                "codespaces": processed_codespaces,
                "count": len(processed_codespaces),
                "success": True
            }

        except Exception as e:
            return {"error": str(e), "codespaces": []}

    def _process_codespace_data(self, cs: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw codespace data for web consumption"""
        # Handle repository field (string vs object)
        repository = cs.get('repository', 'Unknown')
        if isinstance(repository, dict):
            repository = repository.get('full_name', 'Unknown')

        # Process timestamps
        created_at = cs.get('createdAt', cs.get('created_at', ''))
        last_used_at = cs.get('lastUsedAt', cs.get('last_used_at', ''))

        return {
            "name": cs.get('name', 'Unknown'),
            "display_name": cs.get('displayName', cs.get('name', 'Unknown')),
            "repository": repository,
            "state": cs.get('state', 'Unknown'),
            "machine_type": cs.get('machineName', cs.get('machine', {}).get('name', 'Unknown')),
            "created_at": created_at,
            "last_used_at": last_used_at,
            "git_status": cs.get('gitStatus', {}),
            "owner": cs.get('owner', 'Unknown'),
            "web_url": f"https://github.com/codespaces/{cs.get('name', '')}",
            "cost_estimate": self._estimate_cost(cs.get('machineName', 'basicLinux32gb'))
        }

    def _estimate_cost(self, machine_type: str) -> float:
        """Estimate hourly cost for machine type"""
        cost_map = {
            'basicLinux32gb': 0.18,
            'standardLinux32gb': 0.36,
            'premiumLinux64gb': 0.72,
            'largeLinux128gb': 1.44,
        }
        return cost_map.get(machine_type, 0.18)

    async def create_codespace(self, repo: str, branch: str = None,
                             machine: str = None, region: str = None) -> Dict[str, Any]:
        """Create a new codespace"""
        try:
            cmd = ['codespace', 'create', '--repo', repo]

            if branch:
                cmd.extend(['--branch', branch])
            if machine:
                cmd.extend(['--machine', machine])
            if region:
                cmd.extend(['--location', region])

            success, output = await self.run_gh_command(cmd)

            return {
                "success": success,
                "message": output,
                "repository": repo,
                "branch": branch or "main",
                "machine_type": machine or "basicLinux32gb",
                "region": region or "EuropeWest"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def start_codespace(self, codespace_name: str) -> Dict[str, Any]:
        """Start a codespace (via SSH connection)"""
        try:
            # Codespaces auto-start when you connect to them
            success, output = await self.run_gh_command([
                'codespace', 'ssh', '--codespace', codespace_name,
                '--', 'echo "Codespace started successfully"'
            ])

            return {
                "success": success,
                "message": output,
                "codespace_name": codespace_name,
                "action": "start"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def stop_codespace(self, codespace_name: str) -> Dict[str, Any]:
        """Stop a codespace"""
        try:
            success, output = await self.run_gh_command([
                'codespace', 'stop', '--codespace', codespace_name
            ])

            return {
                "success": success,
                "message": output,
                "codespace_name": codespace_name,
                "action": "stop"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_codespace(self, codespace_name: str) -> Dict[str, Any]:
        """Delete a codespace"""
        try:
            success, output = await self.run_gh_command([
                'codespace', 'delete', '--codespace', codespace_name, '--force'
            ])

            return {
                "success": success,
                "message": output,
                "codespace_name": codespace_name,
                "action": "delete"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_repositories(self, limit: int = 20) -> Dict[str, Any]:
        """Get user's repositories"""
        try:
            success, output = await self.run_gh_command([
                'repo', 'list', '--limit', str(limit)
            ])

            if not success:
                return {"error": output, "repositories": []}

            repos = []
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        repos.append({
                            "name": parts[0],
                            "description": parts[1],
                            "visibility": parts[2],
                            "updated_at": parts[3] if len(parts) > 3 else ""
                        })

            return {
                "repositories": repos,
                "count": len(repos),
                "success": True
            }

        except Exception as e:
            return {"error": str(e), "repositories": []}

    async def execute_setup_script(self, codespace_name: str, script: str,
                                 operation_name: str) -> Dict[str, Any]:
        """Execute setup script in codespace"""
        try:
            import time

            # Create unique script name
            prefix = operation_name.lower().replace(' ', '_').replace('/', '_')
            script_name = f'{prefix}_{int(time.time())}.sh'

            # Create script via SSH
            create_cmd = [
                'codespace', 'ssh', '--codespace', codespace_name, '--',
                f"cat > {script_name} << 'SCRIPT_EOF'\n{script}\nSCRIPT_EOF"
            ]

            success, output = await self.run_gh_command(create_cmd)
            if not success:
                return {"success": False, "error": f"Failed to create script: {output}"}

            # Execute script
            exec_cmd = [
                'codespace', 'ssh', '--codespace', codespace_name, '--',
                f'chmod +x {script_name} && bash {script_name} && rm {script_name}'
            ]

            success, output = await self.run_gh_command(exec_cmd)

            return {
                "success": success,
                "output": output,
                "script_name": script_name,
                "operation_name": operation_name
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get codespace metrics using advanced module"""
        try:
            if not self.advanced:
                return {"error": "Advanced metrics not available"}

            # Get metrics (this might need to be made async in the future)
            metrics = self.advanced.get_codespace_metrics()
            return metrics

        except Exception as e:
            return {"error": str(e)}
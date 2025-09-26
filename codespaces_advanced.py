#!/usr/bin/env python3
"""
Advanced Codespaces features: metrics, costs, snapshots, and system monitoring
"""

import subprocess
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class CodespacesAdvanced:
    """Advanced Codespaces operations"""

    def __init__(self, logger, github_manager):
        self.logger = logger
        self.github = github_manager

    def get_codespace_metrics(self, codespace_name: str = None) -> Dict:
        """Get detailed metrics for codespaces"""
        metrics = {
            'codespaces': [],
            'total_cost_estimate': 0.0,
            'total_storage_used': 0,
            'quota_remaining': 'Unknown'
        }

        try:
            # Get codespace list with details
            cmd = ['codespace', 'list', '--json']
            success, output = self.github.run_gh_command(cmd)

            if success:
                codespaces_data = json.loads(output)

                for cs in codespaces_data:
                    cs_metrics = self._get_individual_codespace_metrics(cs)
                    metrics['codespaces'].append(cs_metrics)
                    metrics['total_cost_estimate'] += cs_metrics.get('estimated_cost_per_hour', 0)
                    metrics['total_storage_used'] += cs_metrics.get('storage_used_mb', 0)

        except Exception as e:
            self.logger.error(f"Failed to get codespace metrics: {e}")
            metrics['error'] = str(e)

        return metrics

    def _get_individual_codespace_metrics(self, codespace_data: Dict) -> Dict:
        """Get metrics for a single codespace"""
        metrics = {
            'name': codespace_data.get('name', 'Unknown'),
            'repository': codespace_data.get('repository', {}).get('full_name', 'Unknown'),
            'state': codespace_data.get('state', 'Unknown'),
            'machine_type': codespace_data.get('machine', {}).get('name', 'Unknown'),
            'created_at': codespace_data.get('created_at', 'Unknown'),
            'last_used_at': codespace_data.get('last_used_at', 'Unknown'),
        }

        # Calculate uptime if running
        if metrics['state'] == 'Available':
            try:
                created_time = datetime.fromisoformat(
                    metrics['created_at'].replace('Z', '+00:00')
                )
                uptime = datetime.now() - created_time.replace(tzinfo=None)
                metrics['uptime_hours'] = round(uptime.total_seconds() / 3600, 2)
            except:
                metrics['uptime_hours'] = 0

        # Estimate costs based on machine type
        cost_per_hour = self._get_machine_cost_per_hour(metrics['machine_type'])
        metrics['estimated_cost_per_hour'] = cost_per_hour

        if metrics.get('uptime_hours', 0) > 0:
            metrics['estimated_total_cost'] = round(
                metrics['uptime_hours'] * cost_per_hour, 2
            )

        # Try to get storage information
        try:
            storage_info = self._get_codespace_storage(metrics['name'])
            metrics.update(storage_info)
        except:
            metrics['storage_used_mb'] = 0
            metrics['storage_quota_mb'] = 'Unknown'

        return metrics

    def _get_machine_cost_per_hour(self, machine_type: str) -> float:
        """Get estimated cost per hour for machine type"""
        # GitHub Codespaces pricing (as of 2024, subject to change)
        pricing_map = {
            'basicLinux32gb': 0.18,    # 2-core, 4GB RAM, 32GB storage
            'standardLinux32gb': 0.36,  # 4-core, 8GB RAM, 32GB storage
            'premiumLinux64gb': 0.72,   # 8-core, 16GB RAM, 64GB storage
            'largeLinux128gb': 1.44,    # 16-core, 32GB RAM, 128GB storage
            'default': 0.18
        }

        return pricing_map.get(machine_type, pricing_map['default'])

    def _get_codespace_storage(self, codespace_name: str) -> Dict:
        """Get storage information for a codespace"""
        storage_info = {
            'storage_used_mb': 0,
            'storage_quota_mb': 'Unknown'
        }

        try:
            # This would require SSH access to the codespace to get accurate storage info
            # For now, return placeholder values
            cmd = ['codespace', 'ssh', '--codespace', codespace_name,
                   '--', 'df', '-m', '/workspaces']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    fields = lines[1].split()
                    if len(fields) >= 3:
                        storage_info['storage_used_mb'] = int(fields[2])
                        storage_info['storage_quota_mb'] = int(fields[1])

        except Exception as e:
            self.logger.debug(f"Could not get storage info for {codespace_name}: {e}")

        return storage_info

    def create_codespace_snapshot(self, codespace_name: str, snapshot_name: str = None) -> bool:
        """Create a snapshot/backup of a codespace"""
        if not snapshot_name:
            snapshot_name = f"snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            # GitHub doesn't have direct snapshot API, but we can use commit/push approach
            self.logger.info(f"Creating snapshot of codespace: {codespace_name}")

            # First, ensure the codespace is running
            success, _ = self.github.run_gh_command([
                'codespace', 'ssh', '--codespace', codespace_name,
                '--', 'git', 'add', '.'
            ])

            if success:
                success, _ = self.github.run_gh_command([
                    'codespace', 'ssh', '--codespace', codespace_name,
                    '--', 'git', 'commit', '-m', f"Snapshot: {snapshot_name}"
                ])

                if success:
                    success, output = self.github.run_gh_command([
                        'codespace', 'ssh', '--codespace', codespace_name,
                        '--', 'git', 'push', 'origin'
                    ])

                    if success:
                        self.logger.info(f"Snapshot created successfully: {snapshot_name}")
                        return True

            self.logger.error("Failed to create snapshot")
            return False

        except Exception as e:
            self.logger.error(f"Error creating snapshot: {e}")
            return False

    def setup_port_forwarding(self, codespace_name: str, ports: List[int]) -> bool:
        """Set up port forwarding for a codespace"""
        try:
            for port in ports:
                cmd = ['codespace', 'ports', 'forward',
                       f'{port}:{port}', '--codespace', codespace_name]

                success, output = self.github.run_gh_command(cmd)
                if success:
                    self.logger.info(f"Port {port} forwarded for {codespace_name}")
                else:
                    self.logger.error(f"Failed to forward port {port}: {output}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error setting up port forwarding: {e}")
            return False

    def setup_prebuild(self, repository: str, branch: str = "main") -> bool:
        """Set up prebuild configuration for faster codespace creation"""
        try:
            # This would typically involve creating/updating .devcontainer/prebuild.yml
            # For now, provide a basic implementation

            prebuild_config = {
                "version": "1.0",
                "triggers": {
                    "push": {
                        "branches": [branch]
                    }
                },
                "configuration": ".devcontainer/devcontainer.json"
            }

            self.logger.info(f"Prebuild configuration for {repository} on {branch}")
            # In a real implementation, this would create the prebuild config file
            return True

        except Exception as e:
            self.logger.error(f"Error setting up prebuild: {e}")
            return False

class SystemMonitor:
    """System monitoring and cleanup utilities"""

    def __init__(self, logger):
        self.logger = logger

    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        metrics = {}

        if not PSUTIL_AVAILABLE:
            return self._get_fallback_metrics()

        try:
            # CPU information
            try:
                metrics['cpu'] = {
                    'usage_percent': psutil.cpu_percent(interval=0.1),  # Shorter interval
                    'count': psutil.cpu_count(),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            except (PermissionError, OSError) as e:
                # Fallback for restricted environments
                metrics['cpu'] = {
                    'usage_percent': 'N/A (Permission denied)',
                    'count': psutil.cpu_count() if hasattr(psutil, 'cpu_count') else 'N/A',
                    'load_avg': None
                }

            # Memory information
            try:
                memory = psutil.virtual_memory()
                metrics['memory'] = {
                    'total_mb': round(memory.total / 1024 / 1024),
                    'available_mb': round(memory.available / 1024 / 1024),
                    'used_mb': round(memory.used / 1024 / 1024),
                    'percent_used': memory.percent
                }
            except (PermissionError, OSError) as e:
                metrics['memory'] = self._get_memory_fallback()

            # Disk information
            try:
                disk = psutil.disk_usage('/')
                metrics['disk'] = {
                    'total_gb': round(disk.total / 1024 / 1024 / 1024),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024),
                    'free_gb': round(disk.free / 1024 / 1024 / 1024),
                    'percent_used': round((disk.used / disk.total) * 100, 1)
                }
            except (PermissionError, OSError) as e:
                metrics['disk'] = self._get_disk_fallback()

            # Network information
            try:
                network = psutil.net_io_counters()
                metrics['network'] = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except (PermissionError, OSError, AttributeError):
                metrics['network'] = {'error': 'Not available'}

            # GitHub connectivity test
            metrics['github_connectivity'] = self._test_github_connectivity()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting system metrics: {e}")
            metrics['error'] = str(e)

        return metrics

    def _get_fallback_metrics(self) -> Dict:
        """Get system metrics using command-line tools when psutil isn't available"""
        metrics = {
            'cpu': {'error': 'psutil not available'},
            'memory': self._get_memory_fallback(),
            'disk': self._get_disk_fallback(),
            'network': {'error': 'Not available'},
            'github_connectivity': self._test_github_connectivity()
        }
        return metrics

    def _get_memory_fallback(self) -> Dict:
        """Get memory info using free command"""
        try:
            result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    fields = lines[1].split()
                    if len(fields) >= 4:
                        total_mb = int(fields[1])
                        used_mb = int(fields[2])
                        available_mb = int(fields[3]) if len(fields) > 3 else total_mb - used_mb
                        return {
                            'total_mb': total_mb,
                            'used_mb': used_mb,
                            'available_mb': available_mb,
                            'percent_used': round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0
                        }
        except Exception:
            pass
        return {'error': 'Permission denied'}

    def _get_disk_fallback(self) -> Dict:
        """Get disk info using df command"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    fields = lines[1].split()
                    if len(fields) >= 4:
                        return {
                            'total_gb': fields[1],
                            'used_gb': fields[2],
                            'free_gb': fields[3],
                            'percent_used': fields[4].rstrip('%') if len(fields) > 4 else 'N/A'
                        }
        except Exception:
            pass
        return {'error': 'Permission denied'}

    def _test_github_connectivity(self) -> Dict:
        """Test connectivity to GitHub services"""
        connectivity = {}

        endpoints = {
            'github.com': 'github.com',
            'api.github.com': 'api.github.com',
            'ssh.github.com': 'ssh.github.com'
        }

        for name, endpoint in endpoints.items():
            try:
                start_time = time.time()
                result = subprocess.run(['ping', '-c', '3', endpoint],
                                      capture_output=True, text=True, timeout=10)
                end_time = time.time()

                if result.returncode == 0:
                    # Extract average latency from ping output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'avg' in line:
                            parts = line.split('/')
                            if len(parts) >= 5:
                                avg_latency = float(parts[4])
                                connectivity[name] = {
                                    'status': 'OK',
                                    'latency_ms': avg_latency
                                }
                                break
                    else:
                        connectivity[name] = {
                            'status': 'OK',
                            'latency_ms': round((end_time - start_time) * 1000, 2)
                        }
                else:
                    connectivity[name] = {'status': 'FAILED'}

            except subprocess.TimeoutExpired:
                connectivity[name] = {'status': 'TIMEOUT'}
            except Exception as e:
                connectivity[name] = {'status': f'ERROR: {e}'}

        return connectivity

    def get_cache_usage(self) -> Dict:
        """Get usage information for various caches"""
        cache_info = {}

        home = Path.home()
        cache_dirs = {
            'npm': home / '.npm',
            'pip': home / '.cache/pip',
            'cargo': home / '.cargo',
            'node_modules': home / 'node_modules',
            'git_repos': None  # Will be calculated
        }

        for cache_name, cache_path in cache_dirs.items():
            if cache_name == 'git_repos':
                # Find all .git directories
                total_size = 0
                git_dirs = []
                try:
                    for git_dir in home.glob('**/.git'):
                        if git_dir.is_dir():
                            size = self._get_directory_size(git_dir)
                            total_size += size
                            git_dirs.append(str(git_dir.parent))

                    cache_info[cache_name] = {
                        'size_mb': round(total_size / 1024 / 1024),
                        'count': len(git_dirs),
                        'directories': git_dirs[:10]  # Limit to first 10
                    }
                except Exception as e:
                    cache_info[cache_name] = {'error': str(e)}
            else:
                if cache_path and cache_path.exists():
                    try:
                        size = self._get_directory_size(cache_path)
                        cache_info[cache_name] = {
                            'size_mb': round(size / 1024 / 1024),
                            'path': str(cache_path)
                        }
                    except Exception as e:
                        cache_info[cache_name] = {'error': str(e)}
                else:
                    cache_info[cache_name] = {'size_mb': 0, 'path': 'Not found'}

        return cache_info

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total_size += entry.stat().st_size
        except PermissionError:
            pass  # Skip inaccessible files
        return total_size

    def cleanup_caches(self, cache_types: List[str] = None) -> Dict:
        """Clean up various caches"""
        if cache_types is None:
            cache_types = ['npm', 'pip', 'cargo']

        results = {}

        cleanup_commands = {
            'npm': ['npm', 'cache', 'clean', '--force'],
            'pip': ['pip', 'cache', 'purge'],
            'cargo': ['cargo', 'clean'],
            'yarn': ['yarn', 'cache', 'clean']
        }

        for cache_type in cache_types:
            if cache_type in cleanup_commands:
                try:
                    cmd = cleanup_commands[cache_type]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                    if result.returncode == 0:
                        results[cache_type] = {'status': 'SUCCESS', 'output': result.stdout}
                        self.logger.info(f"Cleaned {cache_type} cache")
                    else:
                        results[cache_type] = {'status': 'FAILED', 'error': result.stderr}
                        self.logger.error(f"Failed to clean {cache_type} cache: {result.stderr}")

                except subprocess.TimeoutExpired:
                    results[cache_type] = {'status': 'TIMEOUT'}
                    self.logger.error(f"Timeout cleaning {cache_type} cache")
                except Exception as e:
                    results[cache_type] = {'status': 'ERROR', 'error': str(e)}
                    self.logger.error(f"Error cleaning {cache_type} cache: {e}")
            else:
                results[cache_type] = {'status': 'UNKNOWN_TYPE'}

        return results

    def cleanup_old_repos(self, days_threshold: int = 30) -> Dict:
        """Clean up old repository clones"""
        home = Path.home()
        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        results = {
            'removed_repos': [],
            'total_size_freed_mb': 0,
            'errors': []
        }

        try:
            for git_dir in home.glob('**/.git'):
                if git_dir.is_dir():
                    repo_path = git_dir.parent

                    # Check last modification time
                    try:
                        last_modified = datetime.fromtimestamp(repo_path.stat().st_mtime)

                        if last_modified < cutoff_date:
                            # Get size before deletion
                            size_bytes = self._get_directory_size(repo_path)
                            size_mb = round(size_bytes / 1024 / 1024)

                            # Remove the repository
                            import shutil
                            shutil.rmtree(repo_path)

                            results['removed_repos'].append({
                                'path': str(repo_path),
                                'size_mb': size_mb,
                                'last_modified': last_modified.isoformat()
                            })
                            results['total_size_freed_mb'] += size_mb

                            self.logger.info(f"Removed old repo: {repo_path} ({size_mb}MB)")

                    except Exception as e:
                        error_msg = f"Error processing {repo_path}: {e}"
                        results['errors'].append(error_msg)
                        self.logger.error(error_msg)

        except Exception as e:
            results['errors'].append(f"General error: {e}")
            self.logger.error(f"Error during repo cleanup: {e}")

        return results

class EnvironmentBootstrapper:
    """Environment setup and bootstrapping"""

    def __init__(self, logger):
        self.logger = logger

    def detect_environment(self) -> Dict:
        """Detect current environment and available tools"""
        env_info = {
            'platform': 'unknown',
            'is_termux': False,
            'is_root': os.geteuid() == 0 if hasattr(os, 'geteuid') else False,
            'available_tools': {},
            'missing_tools': [],
            'recommendations': []
        }

        # Detect platform
        if os.path.exists('/data/data/com.termux'):
            env_info['platform'] = 'termux'
            env_info['is_termux'] = True
        elif os.path.exists('/etc/debian_version'):
            env_info['platform'] = 'debian'
        elif os.path.exists('/etc/redhat-release'):
            env_info['platform'] = 'redhat'
        else:
            env_info['platform'] = 'unknown'

        # Check for essential tools
        essential_tools = {
            'git': 'git --version',
            'gh': 'gh --version',
            'ssh': 'ssh -V',
            'python3': 'python3 --version',
            'node': 'node --version',
            'npm': 'npm --version',
            'rustc': 'rustc --version',
            'cargo': 'cargo --version'
        }

        for tool, version_cmd in essential_tools.items():
            try:
                result = subprocess.run(version_cmd.split(),
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_output = result.stdout.strip() or result.stderr.strip()
                    env_info['available_tools'][tool] = version_output.split('\n')[0]
                else:
                    env_info['missing_tools'].append(tool)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                env_info['missing_tools'].append(tool)

        # Generate recommendations
        if env_info['missing_tools']:
            if env_info['is_termux']:
                env_info['recommendations'].append(
                    f"Install missing tools with: pkg install {' '.join(env_info['missing_tools'])}"
                )
            else:
                env_info['recommendations'].append(
                    "Some essential tools are missing. Install them using your system package manager."
                )

        return env_info

    def bootstrap_termux_environment(self, install_extras: bool = False) -> Dict:
        """Bootstrap Termux environment with essential tools"""
        results = {
            'steps_completed': [],
            'steps_failed': [],
            'total_time_seconds': 0
        }

        start_time = time.time()

        try:
            # Step 1: Update package lists
            self.logger.info("Updating package lists...")
            result = subprocess.run(['pkg', 'update'], capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                results['steps_completed'].append('Package lists updated')
            else:
                results['steps_failed'].append(f'Package update failed: {result.stderr}')
                return results

            # Step 2: Upgrade existing packages
            self.logger.info("Upgrading existing packages...")
            result = subprocess.run(['pkg', 'upgrade', '-y'], capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                results['steps_completed'].append('Packages upgraded')
            else:
                results['steps_failed'].append(f'Package upgrade failed: {result.stderr}')

            # Step 3: Install essential build tools
            essential_packages = [
                'git', 'openssh', 'curl', 'wget', 'clang', 'make',
                'python', 'nodejs', 'rust'
            ]

            for package in essential_packages:
                self.logger.info(f"Installing {package}...")
                result = subprocess.run(['pkg', 'install', '-y', package],
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    results['steps_completed'].append(f'Installed {package}')
                else:
                    results['steps_failed'].append(f'Failed to install {package}: {result.stderr}')

            # Step 4: Install GitHub CLI if not present
            if not shutil.which('gh'):
                self.logger.info("Installing GitHub CLI...")
                result = subprocess.run(['pkg', 'install', '-y', 'gh'],
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    results['steps_completed'].append('Installed GitHub CLI')
                else:
                    results['steps_failed'].append(f'Failed to install GitHub CLI: {result.stderr}')

            # Step 5: Set up Python tools
            self.logger.info("Installing Python development tools...")
            python_tools = ['pip', 'setuptools', 'wheel']
            for tool in python_tools:
                result = subprocess.run(['pip', 'install', '--upgrade', tool],
                                      capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    results['steps_completed'].append(f'Installed Python {tool}')

            # Step 6: Install optional extras
            if install_extras:
                extra_tools = ['docker', 'tmux', 'vim', 'htop']
                for tool in extra_tools:
                    self.logger.info(f"Installing optional tool: {tool}...")
                    result = subprocess.run(['pkg', 'install', '-y', tool],
                                          capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        results['steps_completed'].append(f'Installed optional tool: {tool}')
                    else:
                        results['steps_failed'].append(f'Failed to install {tool}: {result.stderr}')

            # Step 7: Set up storage permissions
            self.logger.info("Requesting storage permissions...")
            try:
                subprocess.run(['termux-setup-storage'], timeout=30)
                results['steps_completed'].append('Storage permissions requested')
            except:
                results['steps_failed'].append('Could not request storage permissions')

        except Exception as e:
            results['steps_failed'].append(f'Bootstrap error: {e}')
            self.logger.error(f"Bootstrap error: {e}")

        results['total_time_seconds'] = round(time.time() - start_time, 2)
        return results

    def setup_development_environment(self, languages: List[str] = None) -> Dict:
        """Set up development environment for specified languages"""
        if languages is None:
            languages = ['python', 'node', 'rust']

        results = {
            'languages_configured': [],
            'configuration_errors': []
        }

        for lang in languages:
            try:
                if lang == 'python':
                    self._setup_python_env(results)
                elif lang == 'node':
                    self._setup_node_env(results)
                elif lang == 'rust':
                    self._setup_rust_env(results)
                else:
                    results['configuration_errors'].append(f'Unknown language: {lang}')
            except Exception as e:
                results['configuration_errors'].append(f'Error configuring {lang}: {e}')

        return results

    def _setup_python_env(self, results: Dict):
        """Set up Python development environment"""
        # Install essential Python packages
        essential_packages = ['virtualenv', 'pip-tools', 'black', 'flake8', 'pytest']

        for package in essential_packages:
            result = subprocess.run(['pip', 'install', '--user', package],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                results['languages_configured'].append(f'Python: {package}')

    def _setup_node_env(self, results: Dict):
        """Set up Node.js development environment"""
        # Install essential Node.js packages
        essential_packages = ['typescript', '@types/node', 'eslint', 'prettier']

        for package in essential_packages:
            result = subprocess.run(['npm', 'install', '-g', package],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                results['languages_configured'].append(f'Node.js: {package}')

    def _setup_rust_env(self, results: Dict):
        """Set up Rust development environment"""
        # Add essential Rust components
        components = ['rustfmt', 'clippy']

        for component in components:
            result = subprocess.run(['rustup', 'component', 'add', component],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                results['languages_configured'].append(f'Rust: {component}')
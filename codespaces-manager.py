#!/usr/bin/env python3
"""
Termux GitHub Codespaces Manager
A comprehensive CLI tool for managing GitHub repositories and Codespaces on Android/Termux
"""

import os
import sys
import json
import subprocess
import shutil
import platform
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import advanced features
try:
    from codespaces_advanced import CodespacesAdvanced, SystemMonitor, EnvironmentBootstrapper
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    print("Warning: Advanced features module not found. Some features will be limited.")

# Configuration
LOGS_DIR = Path.home() / ".local/share/codespaces-manager/logs"
CONFIG_FILE = Path.home() / ".config/codespaces-manager/config.json"
CACHE_DIR = Path.home() / ".cache/codespaces-manager"

# Colors for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

@dataclass
class Config:
    """Configuration settings"""
    default_visibility: str = "private"
    default_branch: str = "main"
    default_license: str = "mit"
    default_machine_type: str = "basicLinux32gb"
    default_region: str = "EuropeWest"
    log_level: str = "INFO"
    auto_confirm: bool = False

class Logger:
    """Simple logging utility"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, message: str):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"

        # Write to file
        with open(self.log_file, "a") as f:
            f.write(log_entry)

        # Print to console with colors
        color = {
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "INFO": Colors.GREEN,
            "DEBUG": Colors.BLUE
        }.get(level, Colors.RESET)

        print(f"{color}[{level}]{Colors.RESET} {message}")

    def error(self, msg): self.log("ERROR", msg)
    def warning(self, msg): self.log("WARNING", msg)
    def info(self, msg): self.log("INFO", msg)
    def debug(self, msg): self.log("DEBUG", msg)

class SystemInfo:
    """System information and diagnostics"""

    @staticmethod
    def is_termux() -> bool:
        return os.path.exists("/data/data/com.termux")

    @staticmethod
    def get_system_info() -> Dict:
        info = {}
        try:
            # System info
            info['uname'] = subprocess.check_output(['uname', '-a'], text=True).strip()
            info['termux'] = SystemInfo.is_termux()

            # Storage info
            df_output = subprocess.check_output(['df', '-h'], text=True)
            info['storage'] = df_output

            # Memory info
            free_output = subprocess.check_output(['free', '-m'], text=True)
            info['memory'] = free_output

            # Network test
            try:
                ping_result = subprocess.check_output(
                    ['ping', '-c', '3', 'api.github.com'],
                    text=True, stderr=subprocess.DEVNULL
                )
                info['github_connectivity'] = "OK"
            except:
                info['github_connectivity'] = "FAILED"

        except Exception as e:
            info['error'] = str(e)

        return info

class GitHubManager:
    """GitHub operations wrapper"""

    def __init__(self, logger: Logger):
        self.logger = logger

    def run_gh_command(self, cmd: List[str], check_auth: bool = True) -> Tuple[bool, str]:
        """Run a gh command and return success status and output"""
        if check_auth and not self.is_authenticated():
            return False, "GitHub CLI not authenticated. Run 'gh auth login' first."

        try:
            result = subprocess.run(['gh'] + cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def is_authenticated(self) -> bool:
        """Check if gh is authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def get_auth_status(self) -> str:
        """Get detailed auth status"""
        success, output = self.run_gh_command(['auth', 'status'], check_auth=False)
        return output if success else "Not authenticated"

class CodespacesManager:
    """Main application class"""

    def __init__(self):
        self.config = self.load_config()
        self.logger = Logger(LOGS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.github = GitHubManager(self.logger)

        # Initialize advanced features if available
        if ADVANCED_FEATURES_AVAILABLE:
            self.codespaces_advanced = CodespacesAdvanced(self.logger, self.github)
            self.system_monitor = SystemMonitor(self.logger)
            self.bootstrapper = EnvironmentBootstrapper(self.logger)
        else:
            self.codespaces_advanced = None
            self.system_monitor = None
            self.bootstrapper = None

    def load_config(self) -> Config:
        """Load configuration from file or create default"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return Config(**data)
            except Exception:
                pass
        return Config()

    def save_config(self):
        """Save current configuration"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config.__dict__, f, indent=2)

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print_header(self):
        """Print application header"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                  GitHub Codespaces Manager                    ║")
        print("║                     for Termux/Android                        ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}")

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation"""
        if self.config.auto_confirm:
            return True

        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"{Colors.YELLOW}? {message}{suffix}: {Colors.RESET}").strip().lower()

        if not response:
            return default
        return response in ['y', 'yes']

    def get_input(self, prompt: str, default: str = "", required: bool = True) -> str:
        """Get user input with default value"""
        display_default = f" [{default}]" if default else ""
        value = input(f"{Colors.BLUE}? {prompt}{display_default}: {Colors.RESET}").strip()

        if not value and default:
            return default
        elif not value and required:
            print(f"{Colors.RED}This field is required.{Colors.RESET}")
            return self.get_input(prompt, default, required)

        return value

    def show_main_menu(self):
        """Display the main menu"""
        self.clear_screen()
        self.print_header()

        print(f"{Colors.BOLD}Main Menu:{Colors.RESET}")
        print(f" {Colors.CYAN} 1.{Colors.RESET} Environment & Diagnostics")
        print(f" {Colors.CYAN} 2.{Colors.RESET} GitHub Auth & SSH")
        print(f" {Colors.CYAN} 3.{Colors.RESET} Repository Operations")
        print(f" {Colors.CYAN} 4.{Colors.RESET} Branch/PR/Issue Operations")
        print(f" {Colors.CYAN} 5.{Colors.RESET} Releases & Tags")
        print(f" {Colors.CYAN} 6.{Colors.RESET} Secrets/Actions/Policies")
        print(f" {Colors.CYAN} 7.{Colors.RESET} Codespaces Lifecycle")
        print(f" {Colors.CYAN} 8.{Colors.RESET} Codespaces Metrics & Costs")
        print(f" {Colors.CYAN} 9.{Colors.RESET} Cleanup & Cache GC")
        print(f" {Colors.CYAN}10.{Colors.RESET} Settings & Profiles")
        print(f" {Colors.CYAN}11.{Colors.RESET} Quick Start Wizard")
        print(f" {Colors.CYAN}12.{Colors.RESET} Uninstall")
        print(f" {Colors.CYAN} 0.{Colors.RESET} Exit")
        print()

    def handle_menu_choice(self, choice: str):
        """Handle main menu selection"""
        menu_handlers = {
            '1': self.environment_menu,
            '2': self.auth_ssh_menu,
            '3': self.repository_menu,
            '4': self.branch_pr_menu,
            '5': self.releases_menu,
            '6': self.secrets_menu,
            '7': self.codespaces_lifecycle_menu,
            '8': self.codespaces_metrics_menu,
            '9': self.cleanup_menu,
            '10': self.settings_menu,
            '11': self.quick_start_wizard,
            '12': self.uninstall,
            '0': self.exit_app
        }

        handler = menu_handlers.get(choice)
        if handler:
            try:
                handler()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
                input("Press Enter to continue...")
        else:
            print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
            input("Press Enter to continue...")

    def environment_menu(self):
        """Environment & Diagnostics menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Environment & Diagnostics{Colors.RESET}\n")

        # Basic system info
        system_info = SystemInfo.get_system_info()

        print(f"{Colors.GREEN}System Information:{Colors.RESET}")
        print(f"System: {system_info.get('uname', 'Unknown')}")
        print(f"Termux: {'Yes' if system_info.get('termux') else 'No'}")
        print(f"GitHub Connectivity: {system_info.get('github_connectivity', 'Unknown')}")
        print()

        # Advanced system metrics if available
        if self.system_monitor:
            metrics = self.system_monitor.get_system_metrics()

            print(f"{Colors.GREEN}System Metrics:{Colors.RESET}")
            if 'cpu' in metrics:
                cpu = metrics['cpu']
                print(f"CPU Usage: {cpu.get('usage_percent', 'N/A')}%")
                print(f"CPU Cores: {cpu.get('count', 'N/A')}")

            if 'memory' in metrics:
                mem = metrics['memory']
                print(f"Memory: {mem.get('used_mb', 'N/A')}MB / {mem.get('total_mb', 'N/A')}MB ({mem.get('percent_used', 'N/A')}%)")

            if 'disk' in metrics:
                disk = metrics['disk']
                print(f"Disk: {disk.get('used_gb', 'N/A')}GB / {disk.get('total_gb', 'N/A')}GB ({disk.get('percent_used', 'N/A')}%)")

            print()

            if 'github_connectivity' in metrics:
                print(f"{Colors.GREEN}GitHub Connectivity Details:{Colors.RESET}")
                for endpoint, status in metrics['github_connectivity'].items():
                    if isinstance(status, dict):
                        latency = status.get('latency_ms', 'N/A')
                        print(f"{endpoint}: {status.get('status', 'Unknown')} ({latency}ms)")
                    else:
                        print(f"{endpoint}: {status}")
                print()

        # GitHub CLI Status
        print(f"{Colors.GREEN}GitHub CLI Status:{Colors.RESET}")
        print(self.github.get_auth_status())
        print()

        # Environment detection if available
        if self.bootstrapper:
            env_info = self.bootstrapper.detect_environment()
            print(f"{Colors.GREEN}Development Environment:{Colors.RESET}")
            print(f"Platform: {env_info.get('platform', 'unknown')}")
            print(f"Available tools: {len(env_info.get('available_tools', {}))}")
            print(f"Missing tools: {', '.join(env_info.get('missing_tools', []))}")

            if env_info.get('recommendations'):
                print(f"\n{Colors.YELLOW}Recommendations:{Colors.RESET}")
                for rec in env_info['recommendations']:
                    print(f"- {rec}")

        input("\nPress Enter to continue...")

    def auth_ssh_menu(self):
        """GitHub Auth & SSH menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}GitHub Auth & SSH{Colors.RESET}\n")

        while True:
            print("1. Check authentication status")
            print("2. Login to GitHub")
            print("3. Generate SSH key")
            print("4. Add SSH key to GitHub")
            print("5. Test SSH connectivity")
            print("6. Bootstrap development environment")
            print("0. Back to main menu")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                print(f"\n{Colors.GREEN}GitHub CLI Status:{Colors.RESET}")
                print(self.github.get_auth_status())
                input("\nPress Enter to continue...")
            elif choice == '2':
                self.github_login()
            elif choice == '3':
                self.generate_ssh_key()
            elif choice == '4':
                self.add_ssh_key_to_github()
            elif choice == '5':
                self.test_ssh_connectivity()
            elif choice == '6':
                self.bootstrap_environment()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")

    def repository_menu(self):
        """Repository Operations menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Repository Operations{Colors.RESET}\n")

        while True:
            print("1. Create repository")
            print("2. List repositories")
            print("3. Clone repository")
            print("4. Fork repository")
            print("5. Delete repository")
            print("6. Archive repository")
            print("7. Transfer repository")
            print("0. Back to main menu")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                self.create_repository()
            elif choice == '2':
                self.list_repositories()
            elif choice == '3':
                self.clone_repository()
            elif choice == '4':
                self.fork_repository()
            elif choice == '5':
                self.delete_repository()
            elif choice == '6':
                self.archive_repository()
            elif choice == '7':
                self.transfer_repository()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")

    def branch_pr_menu(self):
        """Branch/PR/Issue Operations menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Branch/PR/Issue Operations{Colors.RESET}\n")

        while True:
            print("1. Create branch")
            print("2. List branches")
            print("3. Delete branch")
            print("4. Create pull request")
            print("5. List pull requests")
            print("6. Merge pull request")
            print("7. Create issue")
            print("8. List issues")
            print("0. Back to main menu")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                self.create_branch()
            elif choice == '2':
                self.list_branches()
            elif choice == '3':
                self.delete_branch()
            elif choice == '4':
                self.create_pull_request()
            elif choice == '5':
                self.list_pull_requests()
            elif choice == '6':
                self.merge_pull_request()
            elif choice == '7':
                self.create_issue()
            elif choice == '8':
                self.list_issues()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")

    def releases_menu(self):
        """Releases & Tags menu"""
        print(f"{Colors.YELLOW}Releases & Tags menu - Coming soon!{Colors.RESET}")
        input("Press Enter to continue...")

    def secrets_menu(self):
        """Secrets/Actions/Policies menu"""
        print(f"{Colors.YELLOW}Secrets/Actions/Policies menu - Coming soon!{Colors.RESET}")
        input("Press Enter to continue...")

    def codespaces_lifecycle_menu(self):
        """Codespaces Lifecycle menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Codespaces Lifecycle{Colors.RESET}\n")

        while True:
            print("1. Create codespace")
            print("2. List codespaces")
            print("3. Start codespace")
            print("4. Stop codespace")
            print("5. Delete codespace")
            print("6. Rebuild codespace")
            print("7. Connect to codespace")
            print("0. Back to main menu")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                self.create_codespace()
            elif choice == '2':
                self.list_codespaces()
            elif choice == '3':
                self.start_codespace()
            elif choice == '4':
                self.stop_codespace()
            elif choice == '5':
                self.delete_codespace()
            elif choice == '6':
                self.rebuild_codespace()
            elif choice == '7':
                self.connect_to_codespace()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")

    def codespaces_metrics_menu(self):
        """Codespaces Metrics & Costs menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Codespaces Metrics & Costs{Colors.RESET}\n")

        if not self.codespaces_advanced:
            print(f"{Colors.YELLOW}Advanced features not available. Install missing dependencies.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        try:
            print(f"{Colors.GREEN}Retrieving codespace metrics...{Colors.RESET}")
            metrics = self.codespaces_advanced.get_codespace_metrics()

            if 'error' in metrics:
                print(f"{Colors.RED}Error getting metrics: {metrics['error']}{Colors.RESET}")
                input("Press Enter to continue...")
                return

            print(f"{Colors.GREEN}Codespace Summary:{Colors.RESET}")
            print(f"Total Codespaces: {len(metrics.get('codespaces', []))}")
            print(f"Total Storage Used: {metrics.get('total_storage_used', 0)} MB")
            print(f"Estimated Total Cost/Hour: ${metrics.get('total_cost_estimate', 0):.2f}")
            print(f"Quota Remaining: {metrics.get('quota_remaining', 'Unknown')}")
            print()

            if metrics.get('codespaces'):
                print(f"{Colors.GREEN}Individual Codespace Details:{Colors.RESET}")
                for cs in metrics['codespaces']:
                    print(f"\n{Colors.CYAN}Name:{Colors.RESET} {cs.get('name', 'Unknown')}")
                    print(f"Repository: {cs.get('repository', 'Unknown')}")
                    print(f"State: {cs.get('state', 'Unknown')}")
                    print(f"Machine: {cs.get('machine_type', 'Unknown')}")

                    if cs.get('uptime_hours'):
                        print(f"Uptime: {cs['uptime_hours']} hours")

                    if cs.get('estimated_cost_per_hour'):
                        print(f"Cost/Hour: ${cs['estimated_cost_per_hour']:.2f}")

                    if cs.get('estimated_total_cost'):
                        print(f"Estimated Total Cost: ${cs['estimated_total_cost']:.2f}")

                    if cs.get('storage_used_mb'):
                        quota = cs.get('storage_quota_mb', 'Unknown')
                        print(f"Storage: {cs['storage_used_mb']} MB / {quota} MB")

            else:
                print(f"{Colors.YELLOW}No codespaces found.{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error retrieving metrics: {e}{Colors.RESET}")
            self.logger.error(f"Error in codespaces metrics: {e}")

        input("\nPress Enter to continue...")

    def cleanup_menu(self):
        """Cleanup & Cache GC menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Cleanup & Cache GC{Colors.RESET}\n")

        if not self.system_monitor:
            print(f"{Colors.YELLOW}Advanced cleanup features not available.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        while True:
            print("1. Show cache usage")
            print("2. Clean development caches (npm, pip, cargo)")
            print("3. Clean old repository clones")
            print("4. Full system cleanup")
            print("5. Show cleanup recommendations")
            print("0. Back to main menu")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                self.show_cache_usage()
            elif choice == '2':
                self.clean_dev_caches()
            elif choice == '3':
                self.clean_old_repos()
            elif choice == '4':
                self.full_system_cleanup()
            elif choice == '5':
                self.show_cleanup_recommendations()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")

    def show_cache_usage(self):
        """Show current cache usage"""
        print(f"\n{Colors.GREEN}Analyzing cache usage...{Colors.RESET}")

        try:
            cache_info = self.system_monitor.get_cache_usage()

            print(f"\n{Colors.GREEN}Cache Usage Report:{Colors.RESET}")
            total_size = 0

            for cache_type, info in cache_info.items():
                if 'error' in info:
                    print(f"{cache_type}: {Colors.RED}Error - {info['error']}{Colors.RESET}")
                else:
                    size_mb = info.get('size_mb', 0)
                    total_size += size_mb
                    path = info.get('path', 'Unknown')

                    if cache_type == 'git_repos':
                        count = info.get('count', 0)
                        print(f"{cache_type}: {size_mb} MB ({count} repositories)")
                        if info.get('directories'):
                            print(f"  Recent repos: {', '.join(info['directories'][:3])}...")
                    else:
                        print(f"{cache_type}: {size_mb} MB ({path})")

            print(f"\n{Colors.CYAN}Total cache size: {total_size} MB{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error analyzing caches: {e}{Colors.RESET}")

        input("\nPress Enter to continue...")

    def clean_dev_caches(self):
        """Clean development tool caches"""
        print(f"\n{Colors.YELLOW}Clean Development Caches{Colors.RESET}")

        available_caches = ['npm', 'pip', 'cargo', 'yarn']
        selected_caches = []

        print("Select caches to clean:")
        for i, cache_type in enumerate(available_caches, 1):
            print(f"{i}. {cache_type}")

        selections = input(f"{Colors.BLUE}Enter numbers (e.g., 1,2,3) or 'all': {Colors.RESET}").strip()

        if selections.lower() == 'all':
            selected_caches = available_caches
        else:
            try:
                for num in selections.split(','):
                    idx = int(num.strip()) - 1
                    if 0 <= idx < len(available_caches):
                        selected_caches.append(available_caches[idx])
            except ValueError:
                print(f"{Colors.RED}Invalid selection format.{Colors.RESET}")
                input("Press Enter to continue...")
                return

        if not selected_caches:
            print(f"{Colors.YELLOW}No caches selected.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        if self.confirm_action(f"Clean {', '.join(selected_caches)} caches?"):
            try:
                results = self.system_monitor.cleanup_caches(selected_caches)

                print(f"\n{Colors.GREEN}Cleanup Results:{Colors.RESET}")
                for cache_type, result in results.items():
                    status = result.get('status', 'Unknown')
                    if status == 'SUCCESS':
                        print(f"{cache_type}: {Colors.GREEN}✓ Cleaned successfully{Colors.RESET}")
                    else:
                        error = result.get('error', 'Unknown error')
                        print(f"{cache_type}: {Colors.RED}✗ Failed - {error}{Colors.RESET}")

            except Exception as e:
                print(f"{Colors.RED}Error during cleanup: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def clean_old_repos(self):
        """Clean old repository clones"""
        print(f"\n{Colors.YELLOW}Clean Old Repository Clones{Colors.RESET}")

        days_threshold = int(self.get_input("Days since last modification", "30", required=False) or "30")

        print(f"This will remove git repositories not modified in the last {days_threshold} days.")
        if self.confirm_action(f"Proceed with cleanup?"):
            try:
                results = self.system_monitor.cleanup_old_repos(days_threshold)

                print(f"\n{Colors.GREEN}Cleanup Results:{Colors.RESET}")
                print(f"Repositories removed: {len(results.get('removed_repos', []))}")
                print(f"Total space freed: {results.get('total_size_freed_mb', 0)} MB")

                if results.get('removed_repos'):
                    print(f"\nRemoved repositories:")
                    for repo in results['removed_repos'][:10]:  # Show first 10
                        print(f"- {repo['path']} ({repo['size_mb']} MB)")
                    if len(results['removed_repos']) > 10:
                        print(f"... and {len(results['removed_repos']) - 10} more")

                if results.get('errors'):
                    print(f"\n{Colors.YELLOW}Errors encountered:{Colors.RESET}")
                    for error in results['errors'][:5]:  # Show first 5 errors
                        print(f"- {error}")

            except Exception as e:
                print(f"{Colors.RED}Error during cleanup: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def full_system_cleanup(self):
        """Perform comprehensive system cleanup"""
        print(f"\n{Colors.YELLOW}Full System Cleanup{Colors.RESET}")
        print("This will:")
        print("- Clean all development caches")
        print("- Remove old repository clones (30+ days)")
        print("- Clear temporary files")
        print()

        if self.confirm_action("Proceed with full cleanup?"):
            try:
                # Clean dev caches
                print(f"{Colors.GREEN}Cleaning development caches...{Colors.RESET}")
                cache_results = self.system_monitor.cleanup_caches(['npm', 'pip', 'cargo'])

                # Clean old repos
                print(f"{Colors.GREEN}Cleaning old repositories...{Colors.RESET}")
                repo_results = self.system_monitor.cleanup_old_repos(30)

                # Summary
                print(f"\n{Colors.GREEN}Cleanup Summary:{Colors.RESET}")
                cache_success = sum(1 for r in cache_results.values() if r.get('status') == 'SUCCESS')
                print(f"- Development caches: {cache_success}/{len(cache_results)} cleaned")
                print(f"- Old repositories: {len(repo_results.get('removed_repos', []))} removed")
                print(f"- Space freed: {repo_results.get('total_size_freed_mb', 0)} MB")

            except Exception as e:
                print(f"{Colors.RED}Error during full cleanup: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def show_cleanup_recommendations(self):
        """Show cleanup recommendations based on system analysis"""
        print(f"\n{Colors.GREEN}Analyzing system for cleanup recommendations...{Colors.RESET}")

        try:
            cache_info = self.system_monitor.get_cache_usage()
            system_metrics = self.system_monitor.get_system_metrics()

            print(f"\n{Colors.GREEN}Cleanup Recommendations:{Colors.RESET}")

            # Check disk usage
            if 'disk' in system_metrics:
                disk_percent = system_metrics['disk'].get('percent_used', 0)
                if disk_percent > 80:
                    print(f"- {Colors.RED}HIGH PRIORITY:{Colors.RESET} Disk usage is {disk_percent}% - cleanup recommended")
                elif disk_percent > 60:
                    print(f"- {Colors.YELLOW}MEDIUM:{Colors.RESET} Disk usage is {disk_percent}% - consider cleanup")

            # Check cache sizes
            for cache_type, info in cache_info.items():
                if 'size_mb' in info:
                    size_mb = info['size_mb']
                    if cache_type == 'npm' and size_mb > 500:
                        print(f"- NPM cache is large ({size_mb} MB) - consider cleaning")
                    elif cache_type == 'git_repos' and size_mb > 1000:
                        print(f"- Git repositories using {size_mb} MB - check for old repos")
                    elif cache_type == 'cargo' and size_mb > 1000:
                        print(f"- Cargo cache is large ({size_mb} MB) - consider cleaning")

            # Check memory usage
            if 'memory' in system_metrics:
                mem_percent = system_metrics['memory'].get('percent_used', 0)
                if mem_percent > 80:
                    print(f"- {Colors.YELLOW}Memory usage is high ({mem_percent}%) - restart may help{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error generating recommendations: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def settings_menu(self):
        """Settings & Profiles menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Settings & Profiles{Colors.RESET}\n")

        print(f"Current settings:")
        print(f"Default visibility: {self.config.default_visibility}")
        print(f"Default branch: {self.config.default_branch}")
        print(f"Default license: {self.config.default_license}")
        print(f"Default machine type: {self.config.default_machine_type}")
        print(f"Default region: {self.config.default_region}")
        print(f"Auto confirm: {self.config.auto_confirm}")
        print()

        if self.confirm_action("Update settings?"):
            self.update_settings()

        input("Press Enter to continue...")

    def update_settings(self):
        """Update configuration settings"""
        self.config.default_visibility = self.get_input(
            "Default repository visibility",
            self.config.default_visibility,
            required=False
        ) or self.config.default_visibility

        self.config.default_branch = self.get_input(
            "Default branch name",
            self.config.default_branch,
            required=False
        ) or self.config.default_branch

        self.save_config()
        self.logger.info("Settings updated")

    # GitHub CLI operations
    def github_login(self):
        """Login to GitHub"""
        print(f"\n{Colors.GREEN}Starting GitHub login...{Colors.RESET}")
        try:
            subprocess.run(['gh', 'auth', 'login', '--web'], check=True)
            self.logger.info("GitHub authentication successful")
        except subprocess.CalledProcessError:
            self.logger.error("GitHub authentication failed")
        input("Press Enter to continue...")

    def generate_ssh_key(self):
        """Generate SSH key"""
        email = self.get_input("Enter your email address")
        key_name = self.get_input("SSH key name", "id_ed25519_github")

        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(exist_ok=True)

        key_path = ssh_dir / key_name

        try:
            subprocess.run([
                'ssh-keygen', '-t', 'ed25519', '-C', email,
                '-f', str(key_path), '-N', ''
            ], check=True)

            print(f"\n{Colors.GREEN}SSH key generated: {key_path}{Colors.RESET}")
            print(f"Public key: {key_path}.pub")

            # Display public key
            with open(f"{key_path}.pub") as f:
                pubkey = f.read().strip()
            print(f"\n{Colors.CYAN}Public key content:{Colors.RESET}")
            print(pubkey)

            self.logger.info(f"SSH key generated: {key_path}")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"SSH key generation failed: {e}")

        input("\nPress Enter to continue...")

    def add_ssh_key_to_github(self):
        """Add SSH key to GitHub"""
        ssh_dir = Path.home() / ".ssh"
        key_files = list(ssh_dir.glob("*.pub"))

        if not key_files:
            print(f"{Colors.RED}No SSH public keys found in ~/.ssh/{Colors.RESET}")
            input("Press Enter to continue...")
            return

        print("Available SSH keys:")
        for i, key_file in enumerate(key_files, 1):
            print(f"{i}. {key_file.name}")

        try:
            choice = int(input(f"\n{Colors.BLUE}Select key to add (1-{len(key_files)}): {Colors.RESET}")) - 1
            selected_key = key_files[choice]

            title = self.get_input("Key title", f"Termux-{platform.node()}")

            success, output = self.github.run_gh_command([
                'ssh-key', 'add', str(selected_key), '--title', title
            ])

            if success:
                print(f"\n{Colors.GREEN}SSH key added successfully!{Colors.RESET}")
                self.logger.info(f"SSH key added: {selected_key}")
            else:
                print(f"\n{Colors.RED}Failed to add SSH key: {output}{Colors.RESET}")
                self.logger.error(f"Failed to add SSH key: {output}")

        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
        except Exception as e:
            self.logger.error(f"Error adding SSH key: {e}")

        input("Press Enter to continue...")

    def test_ssh_connectivity(self):
        """Test SSH connectivity to GitHub"""
        print(f"\n{Colors.GREEN}Testing SSH connectivity to GitHub...{Colors.RESET}")

        try:
            result = subprocess.run([
                'ssh', '-T', 'git@github.com'
            ], capture_output=True, text=True, timeout=10)

            if "successfully authenticated" in result.stderr:
                print(f"{Colors.GREEN}✓ SSH connection successful!{Colors.RESET}")
                print(result.stderr)
                self.logger.info("SSH connectivity test passed")
            else:
                print(f"{Colors.RED}✗ SSH connection failed{Colors.RESET}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                self.logger.error("SSH connectivity test failed")

        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}✗ SSH connection timed out{Colors.RESET}")
            self.logger.error("SSH connectivity test timed out")
        except Exception as e:
            print(f"{Colors.RED}✗ SSH test error: {e}{Colors.RESET}")
            self.logger.error(f"SSH test error: {e}")

        input("Press Enter to continue...")

    def bootstrap_environment(self):
        """Bootstrap development environment"""
        if not self.bootstrapper:
            print(f"{Colors.YELLOW}Environment bootstrapper not available.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        self.clear_screen()
        print(f"{Colors.BOLD}Bootstrap Development Environment{Colors.RESET}\n")

        # First, detect current environment
        env_info = self.bootstrapper.detect_environment()

        print(f"{Colors.GREEN}Environment Detection:{Colors.RESET}")
        print(f"Platform: {env_info.get('platform', 'unknown')}")
        print(f"Termux: {'Yes' if env_info.get('is_termux') else 'No'}")
        print(f"Root access: {'Yes' if env_info.get('is_root') else 'No'}")
        print(f"Available tools: {len(env_info.get('available_tools', {}))}")
        print(f"Missing tools: {', '.join(env_info.get('missing_tools', []))}")
        print()

        if env_info.get('missing_tools'):
            print(f"{Colors.YELLOW}Missing tools detected. Bootstrap is recommended.{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}All essential tools are available!{Colors.RESET}")

        print()
        print("Bootstrap options:")
        print("1. Quick bootstrap (essential tools only)")
        print("2. Full bootstrap (includes optional tools)")
        print("3. Custom language setup")
        print("0. Back")
        print()

        choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

        if choice == '1':
            self.quick_bootstrap()
        elif choice == '2':
            self.full_bootstrap()
        elif choice == '3':
            self.custom_language_setup()
        elif choice != '0':
            print(f"{Colors.RED}Invalid choice.{Colors.RESET}")
            input("Press Enter to continue...")

    def quick_bootstrap(self):
        """Perform quick bootstrap with essential tools"""
        print(f"\n{Colors.GREEN}Quick Bootstrap - Essential Tools Only{Colors.RESET}")

        if not SystemInfo.is_termux():
            print(f"{Colors.YELLOW}This bootstrap is optimized for Termux. Your mileage may vary.{Colors.RESET}")

        if self.confirm_action("Start quick bootstrap? This may take several minutes."):
            try:
                results = self.bootstrapper.bootstrap_termux_environment(install_extras=False)

                print(f"\n{Colors.GREEN}Bootstrap Results:{Colors.RESET}")
                print(f"Steps completed: {len(results.get('steps_completed', []))}")
                print(f"Steps failed: {len(results.get('steps_failed', []))}")
                print(f"Total time: {results.get('total_time_seconds', 0)} seconds")

                if results.get('steps_completed'):
                    print(f"\n{Colors.GREEN}Completed steps:{Colors.RESET}")
                    for step in results['steps_completed'][-10:]:  # Show last 10
                        print(f"✓ {step}")

                if results.get('steps_failed'):
                    print(f"\n{Colors.RED}Failed steps:{Colors.RESET}")
                    for step in results['steps_failed']:
                        print(f"✗ {step}")

                if not results.get('steps_failed'):
                    print(f"\n{Colors.GREEN}Bootstrap completed successfully!{Colors.RESET}")
                    self.logger.info("Quick bootstrap completed successfully")
                else:
                    print(f"\n{Colors.YELLOW}Bootstrap completed with some failures.{Colors.RESET}")
                    self.logger.warning("Quick bootstrap completed with failures")

            except Exception as e:
                print(f"\n{Colors.RED}Bootstrap failed: {e}{Colors.RESET}")
                self.logger.error(f"Quick bootstrap failed: {e}")

        input("Press Enter to continue...")

    def full_bootstrap(self):
        """Perform full bootstrap with optional tools"""
        print(f"\n{Colors.GREEN}Full Bootstrap - Essential + Optional Tools{Colors.RESET}")

        if not SystemInfo.is_termux():
            print(f"{Colors.YELLOW}This bootstrap is optimized for Termux. Your mileage may vary.{Colors.RESET}")

        print("This will install:")
        print("- All essential development tools")
        print("- Optional tools (docker, tmux, vim, htop)")
        print("- Development language environments")
        print()

        if self.confirm_action("Start full bootstrap? This will take 10-15 minutes."):
            try:
                # Bootstrap system
                results = self.bootstrapper.bootstrap_termux_environment(install_extras=True)

                # Setup development environments
                print(f"\n{Colors.GREEN}Setting up development environments...{Colors.RESET}")
                dev_results = self.bootstrapper.setup_development_environment(['python', 'node', 'rust'])

                print(f"\n{Colors.GREEN}Bootstrap Results:{Colors.RESET}")
                print(f"System steps completed: {len(results.get('steps_completed', []))}")
                print(f"System steps failed: {len(results.get('steps_failed', []))}")
                print(f"Languages configured: {len(dev_results.get('languages_configured', []))}")
                print(f"Total time: {results.get('total_time_seconds', 0)} seconds")

                if results.get('steps_completed'):
                    print(f"\n{Colors.GREEN}System setup completed:{Colors.RESET}")
                    for step in results['steps_completed'][-5:]:  # Show last 5
                        print(f"✓ {step}")

                if dev_results.get('languages_configured'):
                    print(f"\n{Colors.GREEN}Development environments:{Colors.RESET}")
                    for lang in dev_results['languages_configured']:
                        print(f"✓ {lang}")

                if results.get('steps_failed') or dev_results.get('configuration_errors'):
                    print(f"\n{Colors.YELLOW}Some issues encountered - check logs for details.{Colors.RESET}")
                else:
                    print(f"\n{Colors.GREEN}Full bootstrap completed successfully!{Colors.RESET}")
                    self.logger.info("Full bootstrap completed successfully")

            except Exception as e:
                print(f"\n{Colors.RED}Bootstrap failed: {e}{Colors.RESET}")
                self.logger.error(f"Full bootstrap failed: {e}")

        input("Press Enter to continue...")

    def custom_language_setup(self):
        """Setup specific development languages"""
        print(f"\n{Colors.GREEN}Custom Language Setup{Colors.RESET}")

        languages = ['python', 'node', 'rust']
        selected_languages = []

        print("Select languages to configure:")
        for i, lang in enumerate(languages, 1):
            print(f"{i}. {lang}")

        selections = input(f"{Colors.BLUE}Enter numbers (e.g., 1,2) or 'all': {Colors.RESET}").strip()

        if selections.lower() == 'all':
            selected_languages = languages
        else:
            try:
                for num in selections.split(','):
                    idx = int(num.strip()) - 1
                    if 0 <= idx < len(languages):
                        selected_languages.append(languages[idx])
            except ValueError:
                print(f"{Colors.RED}Invalid selection format.{Colors.RESET}")
                input("Press Enter to continue...")
                return

        if not selected_languages:
            print(f"{Colors.YELLOW}No languages selected.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        if self.confirm_action(f"Configure {', '.join(selected_languages)}?"):
            try:
                results = self.bootstrapper.setup_development_environment(selected_languages)

                print(f"\n{Colors.GREEN}Configuration Results:{Colors.RESET}")
                if results.get('languages_configured'):
                    for lang in results['languages_configured']:
                        print(f"✓ {lang}")

                if results.get('configuration_errors'):
                    print(f"\n{Colors.RED}Errors:{Colors.RESET}")
                    for error in results['configuration_errors']:
                        print(f"✗ {error}")

                if not results.get('configuration_errors'):
                    print(f"\n{Colors.GREEN}Language setup completed successfully!{Colors.RESET}")

            except Exception as e:
                print(f"\n{Colors.RED}Language setup failed: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    # Repository operations
    def create_repository(self):
        """Create a new repository"""
        print(f"\n{Colors.GREEN}Create New Repository{Colors.RESET}")

        repo_name = self.get_input("Repository name")
        description = self.get_input("Description", required=False)
        visibility = self.get_input("Visibility (public/private)", self.config.default_visibility)

        cmd = ['repo', 'create', repo_name, '--description', description or '']

        if visibility.lower() == 'private':
            cmd.append('--private')
        else:
            cmd.append('--public')

        if self.confirm_action("Add README?", True):
            cmd.append('--add-readme')

        license_choice = self.get_input("License", self.config.default_license, required=False)
        if license_choice:
            cmd.extend(['--license', license_choice])

        success, output = self.github.run_gh_command(cmd)

        if success:
            print(f"\n{Colors.GREEN}✓ Repository created successfully!{Colors.RESET}")
            print(output)
            self.logger.info(f"Repository created: {repo_name}")
        else:
            print(f"\n{Colors.RED}✗ Failed to create repository: {output}{Colors.RESET}")
            self.logger.error(f"Failed to create repository: {output}")

        input("Press Enter to continue...")

    def list_repositories(self):
        """List repositories"""
        limit = self.get_input("Number of repos to show", "20", required=False)

        cmd = ['repo', 'list', '--limit', limit or '20']
        success, output = self.github.run_gh_command(cmd)

        if success:
            print(f"\n{Colors.GREEN}Your repositories:{Colors.RESET}")
            print(output)
        else:
            print(f"\n{Colors.RED}Failed to list repositories: {output}{Colors.RESET}")

        input("Press Enter to continue...")

    def clone_repository(self):
        """Clone a repository"""
        repo = self.get_input("Repository (owner/name or URL)")

        success, output = self.github.run_gh_command(['repo', 'clone', repo])

        if success:
            print(f"\n{Colors.GREEN}✓ Repository cloned successfully!{Colors.RESET}")
            self.logger.info(f"Repository cloned: {repo}")
        else:
            print(f"\n{Colors.RED}✗ Failed to clone repository: {output}{Colors.RESET}")
            self.logger.error(f"Failed to clone repository: {output}")

        input("Press Enter to continue...")

    def fork_repository(self):
        """Fork a repository"""
        repo = self.get_input("Repository to fork (owner/name)")

        success, output = self.github.run_gh_command(['repo', 'fork', repo])

        if success:
            print(f"\n{Colors.GREEN}✓ Repository forked successfully!{Colors.RESET}")
            print(output)
            self.logger.info(f"Repository forked: {repo}")
        else:
            print(f"\n{Colors.RED}✗ Failed to fork repository: {output}{Colors.RESET}")
            self.logger.error(f"Failed to fork repository: {output}")

        input("Press Enter to continue...")

    def delete_repository(self):
        """Delete a repository"""
        repo = self.get_input("Repository to delete (owner/name)")

        print(f"{Colors.RED}WARNING: This will permanently delete the repository!{Colors.RESET}")
        if self.confirm_action(f"Delete repository '{repo}'?"):
            success, output = self.github.run_gh_command(['repo', 'delete', repo, '--confirm'])

            if success:
                print(f"\n{Colors.GREEN}✓ Repository deleted successfully!{Colors.RESET}")
                self.logger.info(f"Repository deleted: {repo}")
            else:
                print(f"\n{Colors.RED}✗ Failed to delete repository: {output}{Colors.RESET}")
                self.logger.error(f"Failed to delete repository: {output}")

        input("Press Enter to continue...")

    def archive_repository(self):
        """Archive a repository"""
        repo = self.get_input("Repository to archive (owner/name)")

        success, output = self.github.run_gh_command(['repo', 'archive', repo])

        if success:
            print(f"\n{Colors.GREEN}✓ Repository archived successfully!{Colors.RESET}")
            self.logger.info(f"Repository archived: {repo}")
        else:
            print(f"\n{Colors.RED}✗ Failed to archive repository: {output}{Colors.RESET}")
            self.logger.error(f"Failed to archive repository: {output}")

        input("Press Enter to continue...")

    def transfer_repository(self):
        """Transfer repository to another owner"""
        print(f"{Colors.YELLOW}Repository transfer - Coming soon!{Colors.RESET}")
        input("Press Enter to continue...")

    # Branch operations
    def create_branch(self):
        """Create a new branch"""
        branch_name = self.get_input("Branch name")

        try:
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            print(f"\n{Colors.GREEN}✓ Branch '{branch_name}' created and checked out{Colors.RESET}")
            self.logger.info(f"Branch created: {branch_name}")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}✗ Failed to create branch: {e}{Colors.RESET}")
            self.logger.error(f"Failed to create branch: {e}")

        input("Press Enter to continue...")

    def list_branches(self):
        """List branches"""
        try:
            result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True, check=True)
            print(f"\n{Colors.GREEN}Branches:{Colors.RESET}")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}✗ Failed to list branches: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def delete_branch(self):
        """Delete a branch"""
        branch_name = self.get_input("Branch name to delete")

        if self.confirm_action(f"Delete branch '{branch_name}'?"):
            try:
                subprocess.run(['git', 'branch', '-d', branch_name], check=True)
                print(f"\n{Colors.GREEN}✓ Branch '{branch_name}' deleted{Colors.RESET}")
                self.logger.info(f"Branch deleted: {branch_name}")
            except subprocess.CalledProcessError as e:
                print(f"\n{Colors.RED}✗ Failed to delete branch: {e}{Colors.RESET}")
                self.logger.error(f"Failed to delete branch: {e}")

        input("Press Enter to continue...")

    # Pull Request operations
    def create_pull_request(self):
        """Create a pull request"""
        title = self.get_input("PR title")
        body = self.get_input("PR description", required=False)

        cmd = ['pr', 'create', '--title', title]
        if body:
            cmd.extend(['--body', body])

        success, output = self.github.run_gh_command(cmd)

        if success:
            print(f"\n{Colors.GREEN}✓ Pull request created successfully!{Colors.RESET}")
            print(output)
            self.logger.info("Pull request created")
        else:
            print(f"\n{Colors.RED}✗ Failed to create pull request: {output}{Colors.RESET}")
            self.logger.error(f"Failed to create pull request: {output}")

        input("Press Enter to continue...")

    def list_pull_requests(self):
        """List pull requests"""
        success, output = self.github.run_gh_command(['pr', 'list'])

        if success:
            print(f"\n{Colors.GREEN}Pull requests:{Colors.RESET}")
            print(output)
        else:
            print(f"\n{Colors.RED}Failed to list pull requests: {output}{Colors.RESET}")

        input("Press Enter to continue...")

    def merge_pull_request(self):
        """Merge a pull request"""
        pr_number = self.get_input("PR number to merge")

        success, output = self.github.run_gh_command(['pr', 'merge', pr_number, '--squash'])

        if success:
            print(f"\n{Colors.GREEN}✓ Pull request merged successfully!{Colors.RESET}")
            self.logger.info(f"Pull request merged: #{pr_number}")
        else:
            print(f"\n{Colors.RED}✗ Failed to merge pull request: {output}{Colors.RESET}")
            self.logger.error(f"Failed to merge pull request: {output}")

        input("Press Enter to continue...")

    # Issue operations
    def create_issue(self):
        """Create an issue"""
        title = self.get_input("Issue title")
        body = self.get_input("Issue description", required=False)

        cmd = ['issue', 'create', '--title', title]
        if body:
            cmd.extend(['--body', body])

        success, output = self.github.run_gh_command(cmd)

        if success:
            print(f"\n{Colors.GREEN}✓ Issue created successfully!{Colors.RESET}")
            print(output)
            self.logger.info("Issue created")
        else:
            print(f"\n{Colors.RED}✗ Failed to create issue: {output}{Colors.RESET}")
            self.logger.error(f"Failed to create issue: {output}")

        input("Press Enter to continue...")

    def list_issues(self):
        """List issues"""
        success, output = self.github.run_gh_command(['issue', 'list'])

        if success:
            print(f"\n{Colors.GREEN}Issues:{Colors.RESET}")
            print(output)
        else:
            print(f"\n{Colors.RED}Failed to list issues: {output}{Colors.RESET}")

        input("Press Enter to continue...")

    # Codespace operations
    def create_codespace(self):
        """Create a new codespace"""
        print(f"\n{Colors.GREEN}Create New Codespace{Colors.RESET}")

        repo = self.get_input("Repository (owner/name)")
        branch = self.get_input("Branch", self.config.default_branch, required=False)
        machine = self.get_input("Machine type", self.config.default_machine_type, required=False)
        region = self.get_input("Region", self.config.default_region, required=False)

        cmd = ['codespace', 'create', '--repo', repo]

        if branch:
            cmd.extend(['--branch', branch])
        if machine:
            cmd.extend(['--machine', machine])
        if region:
            cmd.extend(['--location', region])

        success, output = self.github.run_gh_command(cmd)

        if success:
            print(f"\n{Colors.GREEN}✓ Codespace created successfully!{Colors.RESET}")
            print(output)
            self.logger.info(f"Codespace created for {repo}")
        else:
            print(f"\n{Colors.RED}✗ Failed to create codespace: {output}{Colors.RESET}")
            self.logger.error(f"Failed to create codespace: {output}")

        input("Press Enter to continue...")

    def list_codespaces(self):
        """List codespaces"""
        success, output = self.github.run_gh_command(['codespace', 'list'])

        if success:
            print(f"\n{Colors.GREEN}Your codespaces:{Colors.RESET}")
            print(output)
        else:
            print(f"\n{Colors.RED}Failed to list codespaces: {output}{Colors.RESET}")

        input("Press Enter to continue...")

    def start_codespace(self):
        """Start a codespace"""
        codespace_name = self.get_input("Codespace name")

        success, output = self.github.run_gh_command(['codespace', 'start', '--codespace', codespace_name])

        if success:
            print(f"\n{Colors.GREEN}✓ Codespace started successfully!{Colors.RESET}")
            self.logger.info(f"Codespace started: {codespace_name}")
        else:
            print(f"\n{Colors.RED}✗ Failed to start codespace: {output}{Colors.RESET}")
            self.logger.error(f"Failed to start codespace: {output}")

        input("Press Enter to continue...")

    def stop_codespace(self):
        """Stop a codespace"""
        codespace_name = self.get_input("Codespace name")

        success, output = self.github.run_gh_command(['codespace', 'stop', '--codespace', codespace_name])

        if success:
            print(f"\n{Colors.GREEN}✓ Codespace stopped successfully!{Colors.RESET}")
            self.logger.info(f"Codespace stopped: {codespace_name}")
        else:
            print(f"\n{Colors.RED}✗ Failed to stop codespace: {output}{Colors.RESET}")
            self.logger.error(f"Failed to stop codespace: {output}")

        input("Press Enter to continue...")

    def delete_codespace(self):
        """Delete a codespace"""
        codespace_name = self.get_input("Codespace name")

        if self.confirm_action(f"Delete codespace '{codespace_name}'?"):
            success, output = self.github.run_gh_command(['codespace', 'delete', '--codespace', codespace_name])

            if success:
                print(f"\n{Colors.GREEN}✓ Codespace deleted successfully!{Colors.RESET}")
                self.logger.info(f"Codespace deleted: {codespace_name}")
            else:
                print(f"\n{Colors.RED}✗ Failed to delete codespace: {output}{Colors.RESET}")
                self.logger.error(f"Failed to delete codespace: {output}")

        input("Press Enter to continue...")

    def rebuild_codespace(self):
        """Rebuild a codespace"""
        codespace_name = self.get_input("Codespace name")

        success, output = self.github.run_gh_command(['codespace', 'rebuild', '--codespace', codespace_name])

        if success:
            print(f"\n{Colors.GREEN}✓ Codespace rebuild started!{Colors.RESET}")
            self.logger.info(f"Codespace rebuild started: {codespace_name}")
        else:
            print(f"\n{Colors.RED}✗ Failed to rebuild codespace: {output}{Colors.RESET}")
            self.logger.error(f"Failed to rebuild codespace: {output}")

        input("Press Enter to continue...")

    def connect_to_codespace(self):
        """Connect to a codespace via SSH"""
        codespace_name = self.get_input("Codespace name")

        print(f"\n{Colors.GREEN}Connecting to codespace '{codespace_name}'...{Colors.RESET}")
        print(f"{Colors.YELLOW}Press Ctrl+D or type 'exit' to disconnect{Colors.RESET}")

        try:
            subprocess.run(['gh', 'codespace', 'ssh', '--codespace', codespace_name])
            print(f"\n{Colors.GREEN}✓ Disconnected from codespace{Colors.RESET}")
            self.logger.info(f"Connected to codespace: {codespace_name}")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Connection interrupted{Colors.RESET}")
        except subprocess.CalledProcessError as e:
            print(f"\n{Colors.RED}✗ Failed to connect: {e}{Colors.RESET}")
            self.logger.error(f"Failed to connect to codespace: {e}")

        input("Press Enter to continue...")

    def quick_start_wizard(self):
        """Quick Start wizard"""
        self.clear_screen()
        print(f"{Colors.BOLD}Quick Start Wizard{Colors.RESET}\n")
        print("This wizard will help you get started quickly:")
        print("1. Check Termux environment")
        print("2. Verify GitHub authentication")
        print("3. Create a sample repository")
        print("4. Create and connect to a codespace")
        print()

        if not self.confirm_action("Start Quick Start wizard?", True):
            return

        # Step 1: Environment check
        print(f"\n{Colors.CYAN}Step 1: Environment Check{Colors.RESET}")
        system_info = SystemInfo.get_system_info()
        if system_info.get('termux'):
            print(f"{Colors.GREEN}✓ Termux environment detected{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Not running in Termux{Colors.RESET}")

        # Step 2: GitHub auth
        print(f"\n{Colors.CYAN}Step 2: GitHub Authentication{Colors.RESET}")
        if self.github.is_authenticated():
            print(f"{Colors.GREEN}✓ GitHub CLI authenticated{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ GitHub CLI not authenticated{Colors.RESET}")
            if self.confirm_action("Login now?"):
                self.github_login()

        # Step 3: Create sample repo
        print(f"\n{Colors.CYAN}Step 3: Create Sample Repository{Colors.RESET}")
        if self.confirm_action("Create a sample repository?", True):
            repo_name = self.get_input("Repository name", f"quickstart-{int(time.time())}")

            success, output = self.github.run_gh_command([
                'repo', 'create', repo_name,
                '--description', 'Created with GitHub Codespaces Manager Quick Start',
                '--private', '--add-readme'
            ])

            if success:
                print(f"{Colors.GREEN}✓ Repository created: {repo_name}{Colors.RESET}")

                # Step 4: Create codespace
                print(f"\n{Colors.CYAN}Step 4: Create Codespace{Colors.RESET}")
                if self.confirm_action("Create a codespace for this repository?", True):

                    username = output.split('/')[-2] if '/' in output else 'unknown'
                    full_repo = f"{username}/{repo_name}"

                    success, cs_output = self.github.run_gh_command([
                        'codespace', 'create', '--repo', full_repo,
                        '--machine', 'basicLinux32gb'
                    ])

                    if success:
                        print(f"{Colors.GREEN}✓ Codespace created successfully!{Colors.RESET}")

                        if self.confirm_action("Connect to the codespace now?", True):
                            # Extract codespace name from output if possible
                            lines = cs_output.strip().split('\n')
                            if lines:
                                codespace_name = lines[0]  # First line usually contains the name
                                self.connect_to_codespace_by_name(codespace_name)
                    else:
                        print(f"{Colors.RED}✗ Failed to create codespace: {cs_output}{Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ Failed to create repository: {output}{Colors.RESET}")

        print(f"\n{Colors.BOLD}Quick Start completed!{Colors.RESET}")
        print("You can now use the main menu to explore more features.")
        input("Press Enter to continue...")

    def connect_to_codespace_by_name(self, codespace_name: str):
        """Connect to codespace by name (helper for quick start)"""
        try:
            subprocess.run(['gh', 'codespace', 'ssh', '--codespace', codespace_name])
        except:
            pass  # Handle silently in quick start

    def uninstall(self):
        """Uninstall the application"""
        print(f"{Colors.RED}Uninstall GitHub Codespaces Manager{Colors.RESET}\n")
        print("This will remove:")
        print("- Configuration files")
        print("- Log files")
        print("- Cache files")
        print("- This script")
        print()

        if self.confirm_action("Proceed with uninstall?"):
            try:
                # Remove config and cache directories
                import shutil
                if CONFIG_FILE.parent.exists():
                    shutil.rmtree(CONFIG_FILE.parent)
                if LOGS_DIR.exists():
                    shutil.rmtree(LOGS_DIR)
                if CACHE_DIR.exists():
                    shutil.rmtree(CACHE_DIR)

                print(f"{Colors.GREEN}✓ Uninstall completed{Colors.RESET}")
                print("You can manually remove this script file if desired.")

            except Exception as e:
                print(f"{Colors.RED}✗ Uninstall failed: {e}{Colors.RESET}")

        input("Press Enter to continue...")

    def exit_app(self):
        """Exit the application"""
        print(f"{Colors.GREEN}Thank you for using GitHub Codespaces Manager!{Colors.RESET}")
        sys.exit(0)

    def run(self):
        """Main application loop"""
        self.logger.info("GitHub Codespaces Manager started")

        try:
            while True:
                self.show_main_menu()
                choice = input(f"{Colors.BLUE}Choose an option (0-12): {Colors.RESET}").strip()
                self.handle_menu_choice(choice)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
            sys.exit(0)

def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description="GitHub Codespaces Manager for Termux")
    parser.add_argument('--version', action='version', version='1.0.0')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode')

    args = parser.parse_args()

    app = CodespacesManager()

    if args.non_interactive:
        app.config.auto_confirm = True

    app.run()

if __name__ == '__main__':
    main()
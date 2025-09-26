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
            print("Press Enter to continue...")

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
            print("8. Language & Development Environment Setup")
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
            elif choice == '8':
                self.language_environment_menu()
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

    def get_repository_selection(self, operation_name="Select repository"):
        """Get repository selection from numbered list"""
        print(f"\n{Colors.GREEN}{operation_name}{Colors.RESET}")

        # Get repository list
        success, output = self.github.run_gh_command(['repo', 'list', '--limit', '50', '--json', 'name,owner'])

        if not success:
            print(f"{Colors.RED}✗ Failed to fetch repositories: {output}{Colors.RESET}")
            input("Press Enter to continue...")
            return None

        try:
            import json
            repos = json.loads(output) if output.strip() else []

            if not repos:
                print(f"{Colors.YELLOW}No repositories found.{Colors.RESET}")
                input("Press Enter to continue...")
                return None

            print(f"\n{Colors.CYAN}Available repositories:{Colors.RESET}")
            for i, repo in enumerate(repos, 1):
                owner = repo.get('owner', {}).get('login', 'Unknown') if isinstance(repo.get('owner'), dict) else repo.get('owner', 'Unknown')
                name = repo.get('name', 'Unknown')
                print(f"{i}. {owner}/{name}")

            print("0. Cancel")
            print()

            while True:
                try:
                    choice = input(f"{Colors.BLUE}Choose repository (1-{len(repos)}): {Colors.RESET}").strip()

                    if choice == '0':
                        return None

                    idx = int(choice) - 1
                    if 0 <= idx < len(repos):
                        selected_repo = repos[idx]
                        owner = selected_repo.get('owner', {}).get('login', 'Unknown') if isinstance(selected_repo.get('owner'), dict) else selected_repo.get('owner', 'Unknown')
                        name = selected_repo.get('name', 'Unknown')
                        return f"{owner}/{name}"
                    else:
                        print(f"{Colors.RED}Invalid choice. Please enter 1-{len(repos)} or 0 to cancel.{Colors.RESET}")

                except ValueError:
                    print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.RESET}")

        except json.JSONDecodeError:
            print(f"{Colors.RED}✗ Failed to parse repository list{Colors.RESET}")
            input("Press Enter to continue...")
            return None

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
        repo = self.get_repository_selection("Select repository to clone")

        if not repo:
            return

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
        repo = self.get_repository_selection("Select repository to fork")

        if not repo:
            return

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
        repo = self.get_repository_selection("Select repository to delete")

        if not repo:
            return

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
        repo = self.get_repository_selection("Select repository to archive")

        if not repo:
            return

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
        repo = self.get_repository_selection("Select repository to transfer")

        if not repo:
            return

        new_owner = self.get_input("New owner username/organization")

        if self.confirm_action(f"Transfer repository '{repo}' to '{new_owner}'?"):
            success, output = self.github.run_gh_command(['repo', 'transfer', repo, new_owner])

            if success:
                print(f"\n{Colors.GREEN}✓ Repository transfer initiated successfully!{Colors.RESET}")
                self.logger.info(f"Repository transferred: {repo} to {new_owner}")
            else:
                print(f"\n{Colors.RED}✗ Failed to transfer repository: {output}{Colors.RESET}")
                self.logger.error(f"Failed to transfer repository: {output}")

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

        # Show available repositories
        print(f"\n{Colors.CYAN}Your available repositories:{Colors.RESET}")
        success, output = self.github.run_gh_command(['repo', 'list', '--limit', '10'])

        if success and output.strip():
            repos = []
            for line in output.strip().split('\n'):
                if line.strip():
                    repo_name = line.split('\t')[0]
                    repos.append(repo_name)
                    print(f"• {repo_name}")
            print()
        else:
            print("Could not fetch repository list")

        repo = self.get_input("Repository (owner/name)")

        # Validate repository exists
        print(f"{Colors.CYAN}Validating repository...{Colors.RESET}")
        validate_success, validate_output = self.github.run_gh_command(['repo', 'view', repo])
        if not validate_success:
            print(f"{Colors.RED}✗ Repository not found or not accessible: {repo}{Colors.RESET}")
            print(f"Please check the repository name and your permissions.")
            input("Press Enter to continue...")
            return

        print(f"{Colors.GREEN}✓ Repository validated{Colors.RESET}")
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
        """Start a codespace by connecting to it (codespaces auto-start on connection)"""
        codespace_name = self.get_input("Codespace name")

        print(f"\n{Colors.CYAN}Connecting to codespace (this will start it automatically)...{Colors.RESET}")

        # GitHub Codespaces auto-start when you connect to them
        success, output = self.github.run_gh_command(['codespace', 'ssh', '--codespace', codespace_name, '--', 'echo "Codespace started successfully"'])

        if success:
            print(f"\n{Colors.GREEN}✓ Codespace started and connected successfully!{Colors.RESET}")
            print(f"{Colors.YELLOW}Note: Codespace '{codespace_name}' is now running.{Colors.RESET}")
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

    def language_environment_menu(self):
        """Language & Development Environment Setup menu"""
        self.clear_screen()
        print(f"{Colors.BOLD}Language & Development Environment Setup{Colors.RESET}\n")
        print(f"{Colors.YELLOW}Configure development environments in your codespaces{Colors.RESET}\n")

        while True:
            print("1. Quick Setup (All Languages + AI Agents)")
            print("2. Individual Language Setup")
            print("3. AI Agents Setup (Claude, Qwen)")
            print("4. Programming Artifacts & Aliases")
            print("5. Development Tools & Extensions")
            print("6. Show Codespace Selection (Arrow Keys)")
            print("7. Execute Remote Setup Commands")
            print("0. Back to codespace lifecycle")
            print()

            choice = input(f"{Colors.BLUE}Choose an option: {Colors.RESET}").strip()

            if choice == '1':
                self.quick_full_environment_setup()
            elif choice == '2':
                self.individual_language_setup()
            elif choice == '3':
                self.ai_agents_setup()
            elif choice == '4':
                self.programming_artifacts_setup()
            elif choice == '5':
                self.development_tools_setup()
            elif choice == '6':
                self.codespace_selector()
            elif choice == '7':
                self.execute_remote_setup()
            elif choice == '0':
                break
            else:
                print(f"{Colors.RED}Invalid choice.{Colors.RESET}")
                input("Press Enter to continue...")

    def get_codespace_selection(self, prompt_text="Select codespace"):
        """Enhanced codespace selection with arrow keys display"""
        success, output = self.github.run_gh_command(['codespace', 'list', '--json', 'name,repository,state,displayName,gitStatus,machineName,lastUsedAt,createdAt,owner'])

        if not success:
            print(f"{Colors.RED}✗ Failed to fetch codespaces: {output}{Colors.RESET}")
            return None

        try:
            import json
            codespaces = json.loads(output) if output.strip() else []

            if not codespaces:
                print(f"{Colors.YELLOW}No codespaces available.{Colors.RESET}")
                return None

            print(f"\n{Colors.BOLD}{prompt_text}:{Colors.RESET}")
            for i, cs in enumerate(codespaces, 1):
                name = cs.get('name', 'Unknown')
                repo = cs.get('repository', 'Unknown')
                if isinstance(repo, dict):
                    repo = repo.get('full_name', 'Unknown')
                state = cs.get('state', 'Unknown')

                state_color = Colors.GREEN if state == 'Available' else Colors.YELLOW
                print(f" {Colors.CYAN}{i}.{Colors.RESET} {name} ({state_color}{state}{Colors.RESET}) → {repo}")

            print()
            choice = input(f"{Colors.BLUE}Select (1-{len(codespaces)}): {Colors.RESET}").strip()

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(codespaces):
                    return codespaces[idx]
            except ValueError:
                pass

            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
            return None

        except json.JSONDecodeError:
            print(f"{Colors.RED}✗ Failed to parse codespace list{Colors.RESET}")
            return None

    def quick_full_environment_setup(self):
        """One-command full environment setup"""
        self.clear_screen()
        print(f"{Colors.BOLD}Quick Full Environment Setup{Colors.RESET}\n")
        print(f"{Colors.GREEN}This will install:{Colors.RESET}")
        print("• Programming Languages: Python, Node.js, Rust, Go, Java")
        print("• AI Agents: Claude CLI, Qwen (Ollama)")
        print("• Development Tools: Git, Docker, VS Code extensions")
        print("• Programming Artifacts: Aliases, shortcuts, dotfiles")
        print()

        codespace = self.get_codespace_selection("Choose codespace for full setup")
        if not codespace:
            return

        codespace_name = codespace['name']
        print(f"\n{Colors.YELLOW}Setting up full environment in: {codespace_name}{Colors.RESET}\n")

        if not self.confirm_action("Proceed with full environment setup?", True):
            return

        # Generate comprehensive setup script
        setup_script = self.generate_full_setup_script()

        print(f"{Colors.GREEN}Executing full environment setup...{Colors.RESET}")

        success = self.execute_script_in_codespace(codespace_name, setup_script, "Full Environment Setup")

        if success:
            print(f"\n{Colors.GREEN}✓ Full environment setup completed successfully!{Colors.RESET}")
            print(f"{Colors.CYAN}Available commands:{Colors.RESET}")
            print("• cl, claude - Claude AI CLI")
            print("• qw, qwen, chat - Qwen AI model")
            print("• python, node, cargo, go, java - Language tools")
            print("• gst, gco, gp - Git aliases")
            print("• ll, la - Directory aliases")

            if self.confirm_action("Connect to codespace to test setup?"):
                self.connect_to_codespace_by_name(codespace_name)
        else:
            print(f"\n{Colors.RED}✗ Full environment setup encountered errors{Colors.RESET}")

        input("Press Enter to continue...")

    def generate_full_setup_script(self):
        """Generate comprehensive environment setup script"""
        return """#!/bin/bash
set -e

echo "🚀 Starting Full Development Environment Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Essential tools
echo "🔧 Installing essential tools..."
sudo apt install -y curl wget git vim tmux htop tree jq unzip build-essential

# Python setup
echo "🐍 Setting up Python environment..."
sudo apt install -y python3 python3-pip python3-venv
python3 -m pip install --upgrade pip
pip3 install poetry black ruff mypy pytest jupyter

# Node.js setup
echo "📦 Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g npm@latest typescript ts-node eslint prettier

# Rust setup
echo "🦀 Installing Rust..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
rustup component add clippy rustfmt

# Go setup
echo "🐹 Installing Go..."
GO_VERSION="1.21.5"
wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
rm go${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc

# Java setup
echo "☕ Installing Java..."
sudo apt install -y openjdk-17-jdk maven gradle

# Claude CLI setup
echo "🤖 Installing Claude CLI..."
if command -v npm >/dev/null 2>&1; then
    npm install -g @anthropic-ai/claude-cli || echo "Claude CLI install failed, continuing..."
fi

# Ollama for Qwen setup
echo "🧠 Installing Ollama for Qwen..."
curl -fsSL https://ollama.ai/install.sh | sh
nohup ollama serve > /dev/null 2>&1 &
sleep 5
ollama pull qwen:latest || echo "Qwen model pull failed, continuing..."

# Docker setup
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Git configuration
echo "📝 Configuring Git..."
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.editor vim

# Helpful aliases
echo "⚡ Setting up aliases and shortcuts..."
cat >> ~/.bashrc << 'EOF'

# Git aliases
alias gst='git status'
alias gco='git checkout'
alias gcb='git checkout -b'
alias gp='git push'
alias gpl='git pull'
alias ga='git add'
alias gc='git commit'
alias gd='git diff'
alias gl='git log --oneline'

# Directory aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Development aliases
alias py='python3'
alias pip='pip3'
alias code='code .'
alias t='tree'
alias h='htop'

# AI aliases (short & full)
alias cl='claude'
alias claude='claude-cli'
alias qw='ollama run qwen'
alias qwen='ollama run qwen'
alias chat='ollama run qwen'

# Quick commands
alias update='sudo apt update && sudo apt upgrade'
alias install='sudo apt install'
alias search='apt search'
alias ports='sudo netstat -tulpn'
alias weather='curl wttr.in'

EOF

# VS Code extensions
echo "💻 Installing VS Code extensions..."
EXTENSIONS=(
    "ms-python.python"
    "rust-lang.rust-analyzer"
    "golang.go"
    "ms-vscode.vscode-typescript-next"
    "bradlc.vscode-tailwindcss"
    "esbenp.prettier-vscode"
    "ms-vscode.vscode-json"
    "redhat.vscode-yaml"
    "ms-azuretools.vscode-docker"
    "github.copilot"
    "anthropic.claude-dev"
)

for ext in "${EXTENSIONS[@]}"; do
    code --install-extension "$ext" --force || echo "Extension $ext failed to install"
done

# Final setup
echo "🎯 Final setup steps..."
source ~/.bashrc

echo "✅ Full Development Environment Setup Complete!"
echo ""
echo "🎉 Available tools and commands:"
echo "Languages: python3, node, cargo, go, java, javac"
echo "AI: claude, qwen (ollama run qwen)"
echo "Git: gst, gco, gp, ga, gc (and standard git)"
echo "Utils: ll, la, t (tree), h (htop)"
echo "Development: code, docker, poetry, npm"
echo ""
echo "🔄 Restart your terminal or run 'source ~/.bashrc' to use aliases"
"""

    def individual_language_setup(self):
        """Setup individual programming languages"""
        self.clear_screen()
        print(f"{Colors.BOLD}Individual Language Setup{Colors.RESET}\n")

        languages = {
            '1': ('Python', self.setup_python),
            '2': ('Node.js', self.setup_nodejs),
            '3': ('Rust', self.setup_rust),
            '4': ('Go', self.setup_go),
            '5': ('Java', self.setup_java),
            '6': ('C/C++', self.setup_cpp),
            '7': ('PHP', self.setup_php),
            '8': ('Ruby', self.setup_ruby)
        }

        for key, (name, _) in languages.items():
            print(f"{key}. {name}")
        print("0. Back")
        print()

        choice = input(f"{Colors.BLUE}Choose language: {Colors.RESET}").strip()

        if choice == '0':
            return

        if choice in languages:
            lang_name, setup_func = languages[choice]

            codespace = self.get_codespace_selection(f"Choose codespace for {lang_name} setup")
            if codespace:
                setup_func(codespace['name'])
        else:
            print(f"{Colors.RED}Invalid choice.{Colors.RESET}")
            input("Press Enter to continue...")

    def setup_python(self, codespace_name):
        """Setup Python environment"""
        script = """#!/bin/bash
echo "🐍 Setting up Python environment..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev
python3 -m pip install --upgrade pip
pip3 install poetry black ruff mypy pytest jupyter pandas numpy requests flask fastapi
echo "✅ Python setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Python Setup")

    def setup_nodejs(self, codespace_name):
        """Setup Node.js environment"""
        script = """#!/bin/bash
echo "📦 Setting up Node.js environment..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g npm@latest typescript ts-node eslint prettier nodemon
echo "✅ Node.js setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Node.js Setup")

    def setup_rust(self, codespace_name):
        """Setup Rust environment"""
        script = """#!/bin/bash
echo "🦀 Setting up Rust environment..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
rustup component add clippy rustfmt
echo "✅ Rust setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Rust Setup")

    def setup_go(self, codespace_name):
        """Setup Go environment"""
        script = """#!/bin/bash
echo "🐹 Setting up Go environment..."
GO_VERSION="1.21.5"
wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
rm go${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
echo "✅ Go setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Go Setup")

    def setup_java(self, codespace_name):
        """Setup Java environment"""
        script = """#!/bin/bash
echo "☕ Setting up Java environment..."
sudo apt update
sudo apt install -y openjdk-17-jdk maven gradle
echo "✅ Java setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Java Setup")

    def setup_cpp(self, codespace_name):
        """Setup C/C++ environment"""
        script = """#!/bin/bash
echo "⚙️ Setting up C/C++ environment..."
sudo apt update
sudo apt install -y build-essential gdb cmake clang-format
echo "✅ C/C++ setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "C/C++ Setup")

    def setup_php(self, codespace_name):
        """Setup PHP environment"""
        script = """#!/bin/bash
echo "🐘 Setting up PHP environment..."
sudo apt update
sudo apt install -y php php-cli php-mbstring php-xml php-curl composer
echo "✅ PHP setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "PHP Setup")

    def setup_ruby(self, codespace_name):
        """Setup Ruby environment"""
        script = """#!/bin/bash
echo "💎 Setting up Ruby environment..."
sudo apt update
sudo apt install -y ruby ruby-dev bundler
gem install rails
echo "✅ Ruby setup complete!"
"""
        self.execute_script_in_codespace(codespace_name, script, "Ruby Setup")

    def ai_agents_setup(self):
        """Setup AI agents (Claude, Qwen)"""
        self.clear_screen()
        print(f"{Colors.BOLD}AI Agents Setup{Colors.RESET}\n")
        print("1. Claude CLI")
        print("2. Qwen (via Ollama)")
        print("3. Both AI Agents")
        print("0. Back")
        print()

        choice = input(f"{Colors.BLUE}Choose option: {Colors.RESET}").strip()

        if choice == '0':
            return

        codespace = self.get_codespace_selection("Choose codespace for AI agents setup")
        if not codespace:
            return

        codespace_name = codespace['name']

        if choice == '1':
            self.setup_claude_cli(codespace_name)
        elif choice == '2':
            self.setup_qwen(codespace_name)
        elif choice == '3':
            self.setup_both_ai_agents(codespace_name)
        else:
            print(f"{Colors.RED}Invalid choice.{Colors.RESET}")
            input("Press Enter to continue...")

    def setup_claude_cli(self, codespace_name):
        """Setup Claude CLI"""
        script = """#!/bin/bash
echo "🤖 Setting up Claude CLI..."
# Install Claude CLI via npm
npm install -g @anthropic-ai/claude-cli || {
    echo "Installing via alternative method..."
    curl -fsSL https://github.com/anthropics/anthropic-cli/releases/latest/download/install.sh | bash
}

# Add aliases for easier access
echo "alias cl='claude'" >> ~/.bashrc
echo "alias claude-cli='claude'" >> ~/.bashrc

echo "✅ Claude CLI setup complete!"
echo "💡 To use: claude --help or cl --help"
echo "⚠️  You'll need to configure your API key: claude config"
"""
        self.execute_script_in_codespace(codespace_name, script, "Claude CLI Setup")

    def setup_qwen(self, codespace_name):
        """Setup Qwen via Ollama"""
        script = """#!/bin/bash
echo "🧠 Setting up Qwen via Ollama..."

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
nohup ollama serve > /dev/null 2>&1 &
sleep 10

# Pull Qwen model
echo "Downloading Qwen model (this may take a while)..."
ollama pull qwen:latest

# Create helpful aliases
echo "alias qw='ollama run qwen'" >> ~/.bashrc
echo "alias qwen='ollama run qwen'" >> ~/.bashrc
echo "alias chat='ollama run qwen'" >> ~/.bashrc

echo "✅ Qwen setup complete!"
echo "💡 To use: qw, qwen or ollama run qwen"
echo "💡 List models: ollama list"
"""
        self.execute_script_in_codespace(codespace_name, script, "Qwen Setup")

    def setup_both_ai_agents(self, codespace_name):
        """Setup both Claude CLI and Qwen"""
        script = """#!/bin/bash
echo "🤖🧠 Setting up both Claude CLI and Qwen..."

# Claude CLI
echo "Setting up Claude CLI..."
npm install -g @anthropic-ai/claude-cli || {
    echo "Installing via alternative method..."
    curl -fsSL https://github.com/anthropics/anthropic-cli/releases/latest/download/install.sh | bash
}

# Ollama and Qwen
echo "Setting up Ollama and Qwen..."
curl -fsSL https://ollama.ai/install.sh | sh
nohup ollama serve > /dev/null 2>&1 &
sleep 10
ollama pull qwen:latest

# Aliases for both AI agents
echo "alias cl='claude'" >> ~/.bashrc
echo "alias claude-cli='claude'" >> ~/.bashrc
echo "alias qw='ollama run qwen'" >> ~/.bashrc
echo "alias qwen='ollama run qwen'" >> ~/.bashrc
echo "alias chat='ollama run qwen'" >> ~/.bashrc

echo "✅ Both AI agents setup complete!"
echo "💡 Claude: claude --help or cl --help"
echo "💡 Qwen: qw, qwen or ollama run qwen"
"""
        self.execute_script_in_codespace(codespace_name, script, "AI Agents Setup")

    def programming_artifacts_setup(self):
        """Setup programming artifacts, aliases, and shortcuts"""
        self.clear_screen()
        print(f"{Colors.BOLD}Programming Artifacts & Aliases Setup{Colors.RESET}\n")

        codespace = self.get_codespace_selection("Choose codespace for programming artifacts")
        if not codespace:
            return

        print(f"\n{Colors.GREEN}Setting up programming artifacts...{Colors.RESET}")

        script = '''#!/bin/bash
echo "⚡ Setting up programming artifacts and aliases..."

# Git aliases and configuration
echo "📝 Configuring Git..."
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.editor vim

# Helpful aliases
echo "⚡ Setting up aliases and shortcuts..."
cat >> ~/.bashrc << "ALIASEOF"

# Git aliases
alias gst='git status'
alias gco='git checkout'
alias gcb='git checkout -b'
alias gp='git push'
alias gpl='git pull'
alias ga='git add'
alias gc='git commit'
alias gd='git diff'
alias gl='git log --oneline'

# Directory aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Development aliases
alias py='python3'
alias pip='pip3'
alias code='code .'
alias t='tree'
alias h='htop'

# AI aliases (short & full)
alias cl='claude'
alias claude='claude-cli'
alias qw='ollama run qwen'
alias qwen='ollama run qwen'
alias chat='ollama run qwen'

# Quick commands
alias update='sudo apt update && sudo apt upgrade'
alias install='sudo apt install'
alias search='apt search'
alias ports='sudo netstat -tulpn'
alias weather='curl wttr.in'

# Make directories and navigate into them
mkcd() { mkdir -p "$1" && cd "$1"; }

ALIASEOF

# Vim configuration
echo "⚙️ Setting up vim configuration..."
cat > ~/.vimrc << "VIMEOF"
set number
set autoindent
set tabstop=4
set shiftwidth=4
syntax on
VIMEOF

echo "✅ Programming artifacts setup complete!"
echo "🔄 Run 'source ~/.bashrc' or restart terminal to activate changes"
'''

        self.execute_script_in_codespace(codespace['name'], script, "Programming Artifacts Setup")

    def development_tools_setup(self):
        """Setup development tools and extensions"""
        self.clear_screen()
        print(f"{Colors.BOLD}Development Tools & Extensions Setup{Colors.RESET}\n")

        codespace = self.get_codespace_selection("Choose codespace for development tools")
        if not codespace:
            return

        script = """#!/bin/bash
echo "🛠️ Installing development tools and VS Code extensions..."

# Essential development tools
echo "Installing development tools..."
sudo apt update
sudo apt install -y curl wget git vim tmux htop tree jq unzip build-essential

# VS Code extensions for enhanced development
echo "📦 Installing VS Code extensions..."
EXTENSIONS=(
    "ms-python.python"
    "ms-python.black-formatter"
    "rust-lang.rust-analyzer"
    "golang.go"
    "ms-vscode.vscode-typescript-next"
    "bradlc.vscode-tailwindcss"
    "esbenp.prettier-vscode"
    "ms-vscode.vscode-json"
    "redhat.vscode-yaml"
    "ms-azuretools.vscode-docker"
    "github.copilot"
    "anthropic.claude-dev"
    "ms-vsliveshare.vsliveshare"
    "ms-vscode.hexeditor"
    "yzhang.markdown-all-in-one"
    "ms-vscode-remote.remote-containers"
    "github.github-vscode-theme"
    "pkief.material-icon-theme"
    "formulahendry.auto-rename-tag"
    "christian-kohler.path-intellisense"
)

for ext in "${EXTENSIONS[@]}"; do
    echo "Installing $ext..."
    code --install-extension "$ext" --force || echo "Failed to install $ext"
done

# Additional useful tools
echo "Installing additional tools..."
# Install gh cli if not present
type gh >/dev/null 2>&1 || {
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh -y
}

echo "✅ Development tools setup complete!"
echo "🎉 Installed VS Code extensions for Python, Rust, Go, TypeScript, and more!"
"""

        self.execute_script_in_codespace(codespace['name'], script, "Development Tools Setup")

    def codespace_selector(self):
        """Interactive codespace selector with arrow keys display"""
        self.clear_screen()
        print(f"{Colors.BOLD}Codespace Selector{Colors.RESET}\n")
        print(f"{Colors.CYAN}Available Codespaces (Arrow Key Navigation Style):{Colors.RESET}\n")

        success, output = self.github.run_gh_command(['codespace', 'list', '--json', 'name,repository,state,displayName,gitStatus,machineName,lastUsedAt,createdAt,owner'])

        if not success:
            print(f"{Colors.RED}✗ Failed to fetch codespaces: {output}{Colors.RESET}")
            input("Press Enter to continue...")
            return

        try:
            import json
            codespaces = json.loads(output) if output.strip() else []

            if not codespaces:
                print(f"{Colors.YELLOW}No codespaces available.{Colors.RESET}")
                input("Press Enter to continue...")
                return

            print(f"{Colors.BOLD}Format: Name (Status) → Repository{Colors.RESET}\n")

            for i, cs in enumerate(codespaces, 1):
                name = cs.get('name', 'Unknown')
                repo = cs.get('repository', 'Unknown')
                if isinstance(repo, dict):
                    repo = repo.get('full_name', 'Unknown')
                state = cs.get('state', 'Unknown')
                machine = cs.get('machine', {}).get('display_name', 'Unknown')

                state_color = Colors.GREEN if state == 'Available' else Colors.YELLOW

                print(f" {Colors.CYAN}▶{Colors.RESET}  {Colors.BOLD}{name}{Colors.RESET}")
                print(f"    Status: {state_color}{state}{Colors.RESET}")
                print(f"    Repository: {repo}")
                print(f"    Machine: {machine}")
                print()

            print(f"{Colors.GREEN}💡 This is how codespaces will be displayed in selection menus{Colors.RESET}")
            print(f"{Colors.YELLOW}Use the number (1, 2, 3...) to select a codespace{Colors.RESET}")

        except json.JSONDecodeError:
            print(f"{Colors.RED}✗ Failed to parse codespace list{Colors.RESET}")

        input("\nPress Enter to continue...")

    def execute_remote_setup(self):
        """Execute custom setup commands in a codespace"""
        self.clear_screen()
        print(f"{Colors.BOLD}Execute Remote Setup Commands{Colors.RESET}\n")

        codespace = self.get_codespace_selection("Choose codespace for remote execution")
        if not codespace:
            return

        codespace_name = codespace['name']

        print(f"\n{Colors.YELLOW}Enter commands to execute in {codespace_name}:{Colors.RESET}")
        print(f"{Colors.CYAN}(Enter empty line to finish, 'exit' to cancel){Colors.RESET}\n")

        commands = []
        while True:
            cmd = input(f"{Colors.BLUE}Command: {Colors.RESET}").strip()
            if not cmd:
                break
            if cmd.lower() == 'exit':
                return
            commands.append(cmd)

        if not commands:
            print(f"{Colors.YELLOW}No commands entered.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        # Create script from commands
        script = "#!/bin/bash\nset -e\n\n" + "\n".join(commands)

        print(f"\n{Colors.GREEN}Executing {len(commands)} commands...{Colors.RESET}")
        self.execute_script_in_codespace(codespace_name, script, "Custom Commands")

    def execute_script_in_codespace(self, codespace_name, script, operation_name):
        """Execute a script in the specified codespace"""
        try:
            print(f"{Colors.YELLOW}Executing {operation_name} in {codespace_name}...{Colors.RESET}")

            # Create a temporary script file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                temp_script = f.name

            # Debug: Show script size and first few lines
            print(f"{Colors.CYAN}Script size: {len(script)} bytes{Colors.RESET}")
            script_lines = script.split('\n')
            print(f"{Colors.CYAN}Script preview (first 5 lines):{Colors.RESET}")
            for i, line in enumerate(script_lines[:5]):
                print(f"  {i+1}: {line}")
            if len(script_lines) > 5:
                print(f"  ... ({len(script_lines)} total lines)")

            # Copy script to codespace and execute
            # First, determine the working directory and create script path
            # Use unique filename and create script directly via SSH
            import time
            # Create appropriate prefix based on operation name
            prefix = operation_name.lower().replace(' ', '_').replace('/', '_')
            script_name = f'{prefix}_{int(time.time())}.sh'

            # Escape the script content for safe transfer
            script_escaped = script.replace("'", "'\"'\"'").replace("\n", "\\n")

            # Create script directly via SSH instead of using cp
            create_cmd = ['gh', 'codespace', 'ssh', '--codespace', codespace_name, '--',
                         f"cat > {script_name} << 'SCRIPT_EOF'\n{script}\nSCRIPT_EOF"]

            print(f"Creating script in codespace as {script_name}...")
            create_result = subprocess.run(create_cmd, capture_output=True, text=True)

            if create_result.returncode != 0:
                print(f"{Colors.RED}✗ Failed to create script: {create_result.stderr}{Colors.RESET}")
                return False
            else:
                print(f"{Colors.GREEN}✓ Script created successfully{Colors.RESET}")

            # Verify the script was created
            verify_cmd = ['gh', 'codespace', 'ssh', '--codespace', codespace_name, '--', f'ls -la {script_name} && wc -l {script_name}']
            print(f"Verifying script creation...")
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)

            if verify_result.returncode == 0:
                print(f"{Colors.CYAN}Verification: {verify_result.stdout}{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}Verification failed: {verify_result.stderr}{Colors.RESET}")
                return False

            # Execute the script
            exec_cmd = ['gh', 'codespace', 'ssh', '--codespace', codespace_name, '--', f'chmod +x {script_name} && bash {script_name} && rm {script_name}']
            print(f"Executing setup script...")
            exec_result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout

            # Clean up temp file
            os.unlink(temp_script)

            if exec_result.returncode == 0:
                print(f"{Colors.GREEN}✓ {operation_name} completed successfully!{Colors.RESET}")
                if exec_result.stdout:
                    print(f"\n{Colors.CYAN}Output:{Colors.RESET}")
                    # Show first and last few lines of output for debugging
                    output_lines = exec_result.stdout.strip().split('\n')
                    if len(output_lines) <= 20:
                        print(exec_result.stdout)
                    else:
                        print('\n'.join(output_lines[:10]))
                        print(f"\n{Colors.YELLOW}... ({len(output_lines)} total lines) ...{Colors.RESET}\n")
                        print('\n'.join(output_lines[-5:]))
                return True
            else:
                print(f"{Colors.RED}✗ {operation_name} failed!{Colors.RESET}")
                if exec_result.stderr:
                    print(f"\n{Colors.RED}Error:{Colors.RESET}")
                    print(exec_result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}✗ {operation_name} timed out (10 minutes){Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.RED}✗ Error executing {operation_name}: {e}{Colors.RESET}")
            return False
        finally:
            # Cleanup remote script
            try:
                subprocess.run(['gh', 'codespace', 'ssh', '--codespace', codespace_name, '--', 'rm -f /tmp/setup_script.sh'],
                             capture_output=True, timeout=30)
            except:
                pass  # Ignore cleanup errors

        input("Press Enter to continue...")

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
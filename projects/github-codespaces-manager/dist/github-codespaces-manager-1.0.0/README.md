# GitHub Codespaces Manager for Termux

A comprehensive command-line interface for managing GitHub repositories and Codespaces on Android devices using Termux.

## Features

### 🔧 Core Functionality
- **Full GitHub integration** - Manage repositories, branches, PRs, issues, and releases
- **Codespaces lifecycle management** - Create, start, stop, rebuild, and connect to codespaces
- **SSH key management** - Generate, add, and test SSH keys for GitHub
- **Environment bootstrapping** - Automated setup of development tools
- **System monitoring** - Real-time metrics and cleanup recommendations

### 📊 Advanced Features
- **Cost tracking** - Monitor codespace usage and estimated costs
- **Cache management** - Clean npm, pip, cargo, and other development caches
- **Storage optimization** - Automatic cleanup of old repository clones
- **Performance monitoring** - CPU, memory, disk, and network metrics
- **Development environment setup** - Python, Node.js, and Rust toolchains

### 🛠️ Supported Operations

#### Repository Management
- Create public/private repositories with templates
- Clone, fork, and transfer repositories
- Archive and delete repositories
- Set up repository secrets and variables

#### Branch & Pull Request Operations
- Create and manage branches
- Create, review, and merge pull requests
- Issue tracking and milestone management
- CODEOWNERS and template management

#### Codespaces Features
- Multi-region codespace deployment
- Custom devcontainer configuration
- Port forwarding and snapshot management
- Resource monitoring and cost estimation
- Prebuild configuration for faster startup

#### System Administration
- Termux environment detection and optimization
- Development tool installation (git, gh, node, python, rust)
- Cache cleanup and storage management
- Network connectivity testing
- Automated system health checks

## Installation

### Prerequisites
- Android device with Termux installed
- Internet connection
- Storage permission (requested automatically)

### Quick Installation

1. **Install Termux** from F-Droid or Google Play Store

2. **Grant storage permission**:
   ```bash
   termux-setup-storage
   ```

3. **Download and run the manager**:
   ```bash
   # Download the script
   curl -L -o codespaces-manager.py https://raw.githubusercontent.com/your-repo/codespaces-manager.py
   curl -L -o codespaces_advanced.py https://raw.githubusercontent.com/your-repo/codespaces_advanced.py

   # Make executable
   chmod +x codespaces-manager.py

   # Install dependencies
   pkg update && pkg upgrade
   pkg install python python-pip git openssh
   pip install psutil

   # Run the application
   ./codespaces-manager.py
   ```

### Automatic Bootstrap
The application includes an automated bootstrap feature that will:
- Detect your Termux environment
- Install missing essential tools
- Configure development environments
- Set up GitHub CLI authentication

Simply select **"Quick Start Wizard"** from the main menu for guided setup.

## Usage

### Main Menu Navigation
```
Main Menu:
 1. Environment & Diagnostics    - System info and health checks
 2. GitHub Auth & SSH           - Authentication and key management
 3. Repository Operations       - Create, clone, manage repos
 4. Branch/PR/Issue Operations  - Git workflows and collaboration
 5. Releases & Tags             - Version management
 6. Secrets/Actions/Policies    - Security and automation settings
 7. Codespaces Lifecycle        - Create and manage codespaces
 8. Codespaces Metrics & Costs  - Monitor usage and expenses
 9. Cleanup & Cache GC          - System maintenance and optimization
10. Settings & Profiles         - Configuration management
11. Quick Start Wizard          - Automated setup process
12. Uninstall                   - Remove application and data
```

### Common Workflows

#### First-Time Setup
1. Run `./codespaces-manager.py`
2. Select **"Quick Start Wizard"** (option 11)
3. Follow the automated setup process
4. Authentication with GitHub will be handled automatically

#### Creating a Repository and Codespace
1. **GitHub Auth & SSH** → Login to GitHub
2. **Repository Operations** → Create repository
   - Enter name, description, visibility
   - Choose license and README options
3. **Codespaces Lifecycle** → Create codespace
   - Select machine type (basicLinux32gb recommended)
   - Choose region (EuropeWest, WestUs2, etc.)
   - Configure devcontainer if needed
4. **Codespaces Lifecycle** → Connect to codespace

#### System Maintenance
1. **Environment & Diagnostics** → View system status
2. **Cleanup & Cache GC** → Run cleanup recommendations
3. **Codespaces Metrics & Costs** → Monitor resource usage

### Command Line Options
```bash
# Show version
./codespaces-manager.py --version

# Run in non-interactive mode (uses defaults)
./codespaces-manager.py --non-interactive

# Display help
./codespaces-manager.py --help
```

## Configuration

### Settings File Location
- Configuration: `~/.config/codespaces-manager/config.json`
- Logs: `~/.local/share/codespaces-manager/logs/`
- Cache: `~/.cache/codespaces-manager/`

### Default Configuration
```json
{
  "default_visibility": "private",
  "default_branch": "main",
  "default_license": "mit",
  "default_machine_type": "basicLinux32gb",
  "default_region": "EuropeWest",
  "log_level": "INFO",
  "auto_confirm": false
}
```

### Customizable Defaults
- Repository visibility (public/private)
- Default branch name
- License template
- Codespace machine type and region
- Logging verbosity
- Confirmation prompts

## Machine Types & Pricing

| Machine Type | Specs | Est. Cost/Hour |
|--------------|-------|----------------|
| basicLinux32gb | 2-core, 4GB RAM, 32GB | $0.18 |
| standardLinux32gb | 4-core, 8GB RAM, 32GB | $0.36 |
| premiumLinux64gb | 8-core, 16GB RAM, 64GB | $0.72 |
| largeLinux128gb | 16-core, 32GB RAM, 128GB | $1.44 |

*Pricing estimates based on GitHub's current rates and subject to change*

## Advanced Features

### System Monitoring
The application provides comprehensive system monitoring:
- **CPU Usage** - Real-time processor utilization
- **Memory Stats** - RAM usage and availability
- **Disk Space** - Storage consumption and free space
- **Network Tests** - Connectivity to GitHub services with latency
- **Cache Analysis** - Development tool cache sizes

### Cleanup & Optimization
Automated cleanup features include:
- **Development Caches** - npm, pip, cargo, yarn cache clearing
- **Old Repositories** - Automatic removal of stale git clones
- **Temporary Files** - System temp directory cleanup
- **Recommendations** - Intelligent suggestions based on usage patterns

### Environment Bootstrap
The bootstrap system can automatically install and configure:

**Essential Tools:**
- Git with GitHub CLI (gh)
- SSH client and key management
- Build essentials (clang, make)
- Core utilities (curl, wget)

**Language Environments:**
- **Python** - pip, virtualenv, essential packages
- **Node.js** - npm, TypeScript, development tools
- **Rust** - rustc, cargo, clippy, rustfmt

**Optional Tools:**
- Docker CLI (if available)
- Terminal multiplexers (tmux)
- Editors (vim)
- System monitors (htop)

## Troubleshooting

### Common Issues

#### "Advanced features not available"
- Install psutil: `pip install psutil`
- Ensure codespaces_advanced.py is in the same directory

#### Authentication problems
- Run `gh auth login` manually
- Check internet connectivity
- Verify GitHub CLI installation: `gh --version`

#### SSH connection failures
- Generate new SSH key through the application
- Add key to GitHub account
- Test connectivity: **GitHub Auth & SSH** → Test SSH connectivity

#### Permission denied errors
- Grant Termux storage permission
- Check file permissions: `chmod +x codespaces-manager.py`
- Run without root privileges

#### Slow performance
- Use cleanup features to free up disk space
- Check system metrics for resource constraints
- Consider using smaller codespace machine types

### Debug Mode
Enable debug logging by editing the configuration file:
```json
{
  "log_level": "DEBUG"
}
```

Logs are stored in `~/.local/share/codespaces-manager/logs/`

### Getting Help
- Check the diagnostics menu for system health
- Review log files for detailed error information
- Ensure all prerequisites are installed
- Try the Quick Start wizard for automated fixes

## Security Considerations

### Authentication
- GitHub CLI handles secure token storage
- SSH keys are generated locally and never shared
- All API calls use official GitHub CLI commands

### Data Privacy
- No usage data is transmitted outside GitHub's APIs
- Local configuration files contain no sensitive information
- SSH keys remain on device unless explicitly added to GitHub

### Network Security
- All connections use HTTPS/SSH encryption
- No third-party services are contacted
- GitHub API calls are authenticated and rate-limited

## Contributing

This tool is designed to be extensible and maintainable:

### Project Structure
- `codespaces-manager.py` - Main application and UI
- `codespaces_advanced.py` - Advanced features and system monitoring
- `README.md` - Documentation and usage guide

### Development Setup
1. Clone the repository
2. Install development dependencies
3. Test in a clean Termux environment
4. Follow existing code patterns and conventions

## License

This project is available under the MIT License. See LICENSE file for details.

## Support

For issues, feature requests, or questions:
- Review the troubleshooting guide above
- Check existing issues and documentation
- Use the built-in diagnostic tools
- Test with the Quick Start wizard

---

**Note**: This tool requires active GitHub account and may incur costs for Codespaces usage. Monitor your usage through the metrics dashboard and GitHub's billing page.
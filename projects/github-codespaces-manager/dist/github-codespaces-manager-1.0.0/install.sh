#!/usr/bin/env bash
set -e

# GitHub Codespaces Manager Installation Script for Termux
# This script will install all dependencies and set up the application

echo "🚀 GitHub Codespaces Manager - Installation Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_warning "This installer is optimized for Termux on Android"
    print_warning "Some features may not work correctly on other systems"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_step "Checking prerequisites..."

# Check for storage permission
if command -v termux-setup-storage >/dev/null 2>&1; then
    print_status "Termux detected - ensuring storage permission..."
    termux-setup-storage 2>/dev/null || print_warning "Storage permission may need to be granted manually"
fi

print_step "Updating package repositories..."
if command -v pkg >/dev/null 2>&1; then
    pkg update -y || {
        print_error "Failed to update package repositories"
        exit 1
    }
else
    print_warning "pkg command not found - trying alternative package managers"
    if command -v apt >/dev/null 2>&1; then
        apt update -y
    elif command -v yum >/dev/null 2>&1; then
        yum update -y
    fi
fi

print_step "Installing essential packages..."
ESSENTIAL_PACKAGES=(
    "python"
    "python-pip"
    "git"
    "openssh"
    "curl"
    "wget"
)

for package in "${ESSENTIAL_PACKAGES[@]}"; do
    if command -v pkg >/dev/null 2>&1; then
        print_status "Installing $package..."
        pkg install -y "$package" || print_warning "Failed to install $package"
    else
        print_status "Attempting to install $package with system package manager..."
        if command -v apt >/dev/null 2>&1; then
            apt install -y "$package" 2>/dev/null || true
        elif command -v yum >/dev/null 2>&1; then
            yum install -y "$package" 2>/dev/null || true
        fi
    fi
done

# Install GitHub CLI
print_step "Installing GitHub CLI..."
if ! command -v gh >/dev/null 2>&1; then
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y gh || print_warning "Failed to install GitHub CLI through pkg"
    else
        print_warning "GitHub CLI installation may require manual setup"
    fi
else
    print_status "GitHub CLI already installed"
fi

# Install Python dependencies
print_step "Installing Python dependencies..."
PYTHON_PACKAGES=(
    "psutil"
    "requests"
)

for package in "${PYTHON_PACKAGES[@]}"; do
    print_status "Installing Python package: $package"
    pip install --upgrade "$package" || print_warning "Failed to install $package"
done

# Download application files
print_step "Setting up application files..."
SCRIPT_DIR="$HOME"
MAIN_SCRIPT="$SCRIPT_DIR/codespaces-manager.py"
ADVANCED_MODULE="$SCRIPT_DIR/codespaces_advanced.py"

# Check if files already exist
if [ -f "$MAIN_SCRIPT" ]; then
    print_status "Main script already exists at $MAIN_SCRIPT"
else
    print_warning "Main script not found - please ensure codespaces-manager.py is in $SCRIPT_DIR"
fi

if [ -f "$ADVANCED_MODULE" ]; then
    print_status "Advanced module already exists at $ADVANCED_MODULE"
else
    print_warning "Advanced module not found - please ensure codespaces_advanced.py is in $SCRIPT_DIR"
fi

# Make scripts executable
if [ -f "$MAIN_SCRIPT" ]; then
    chmod +x "$MAIN_SCRIPT"
    print_status "Made main script executable"
fi

# Create necessary directories
print_step "Creating configuration directories..."
mkdir -p "$HOME/.config/codespaces-manager"
mkdir -p "$HOME/.local/share/codespaces-manager/logs"
mkdir -p "$HOME/.cache/codespaces-manager"
print_status "Configuration directories created"

# Create symlink for easy access
if [ -f "$MAIN_SCRIPT" ]; then
    SYMLINK_PATH="$HOME/../usr/bin/codespaces-manager"
    if [ -L "$SYMLINK_PATH" ]; then
        rm "$SYMLINK_PATH"
    fi
    ln -sf "$MAIN_SCRIPT" "$SYMLINK_PATH" 2>/dev/null || print_warning "Could not create symlink"
    if [ -L "$SYMLINK_PATH" ]; then
        print_status "Created symlink: 'codespaces-manager' command available"
    fi
fi

# Test installation
print_step "Testing installation..."
if [ -f "$MAIN_SCRIPT" ]; then
    if python3 "$MAIN_SCRIPT" --version >/dev/null 2>&1; then
        print_status "✓ Application test passed"
    else
        print_warning "Application test failed - check dependencies"
    fi
fi

# Check command availability
print_step "Verifying installed tools..."
TOOLS_TO_CHECK=("python3" "git" "gh" "ssh")
for tool in "${TOOLS_TO_CHECK[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        VERSION=$($tool --version 2>&1 | head -n1 | cut -d' ' -f1-3 2>/dev/null || echo "unknown version")
        print_status "✓ $tool: $VERSION"
    else
        print_warning "✗ $tool: not found"
    fi
done

echo
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo
echo "Next steps:"
echo "1. Run the application: ${CYAN}./codespaces-manager.py${NC}"
echo "2. Or use the command: ${CYAN}codespaces-manager${NC} (if symlink was created)"
echo "3. Select 'Quick Start Wizard' for initial setup"
echo "4. Authenticate with GitHub when prompted"
echo

# Offer to run Quick Start
read -p "Run the application now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if [ -f "$MAIN_SCRIPT" ]; then
        print_status "Starting GitHub Codespaces Manager..."
        exec python3 "$MAIN_SCRIPT"
    else
        print_error "Main script not found. Please check installation."
    fi
fi

print_status "Installation script completed successfully!"
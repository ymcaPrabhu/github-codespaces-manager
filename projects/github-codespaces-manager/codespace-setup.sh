#!/bin/bash

# 🚀 Complete Development Environment Setup for GitHub Codespaces/Linux
# Compatible with Ubuntu/Debian-based systems
# Sets up languages, tools, AI assistants, and useful shortcuts

set -e  # Exit on any error

echo "🚀 Starting development environment setup for Linux/Codespace..."
echo "This will install: Rust, Python, Node.js, TypeScript, uv, cargo, npm, GitHub CLI, AI tools, and more!"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Detect package manager
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    UPDATE_CMD="sudo apt update && sudo apt upgrade -y"
    INSTALL_CMD="sudo apt install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    UPDATE_CMD="sudo yum update -y"
    INSTALL_CMD="sudo yum install -y"
elif command -v pkg &> /dev/null; then
    PKG_MANAGER="pkg"
    UPDATE_CMD="pkg update -y && pkg upgrade -y"
    INSTALL_CMD="pkg install -y"
else
    log_error "No supported package manager found"
    exit 1
fi

log_info "Detected package manager: $PKG_MANAGER"

# =============================================================================
# SYSTEM UPDATE AND BASIC TOOLS
# =============================================================================

log_info "Updating system packages..."
eval $UPDATE_CMD

log_info "Installing essential tools..."
if [[ "$PKG_MANAGER" == "apt" ]]; then
    $INSTALL_CMD curl wget git vim nano htop tree jq unzip zip tar gzip build-essential
elif [[ "$PKG_MANAGER" == "yum" ]]; then
    $INSTALL_CMD curl wget git vim nano htop tree jq unzip zip tar gzip gcc gcc-c++ make
else
    $INSTALL_CMD curl wget git vim nano htop tree jq unzip zip tar gzip
fi

log_success "System update and basic tools installed"

# =============================================================================
# PROGRAMMING LANGUAGES
# =============================================================================

log_info "Installing Python (latest stable)..."
if [[ "$PKG_MANAGER" == "apt" ]]; then
    $INSTALL_CMD python3 python3-pip python3-venv python3-dev
    # Create python symlink if it doesn't exist
    if ! command -v python &> /dev/null; then
        sudo ln -sf /usr/bin/python3 /usr/local/bin/python
    fi
    # Ensure pip is available as 'pip'
    if ! command -v pip &> /dev/null; then
        sudo ln -sf /usr/bin/pip3 /usr/local/bin/pip
    fi
else
    $INSTALL_CMD python python-pip
fi

python -m pip install --user --upgrade pip

log_info "Installing Node.js and npm..."
# Install Node.js via NodeSource repository for latest LTS
if [[ "$PKG_MANAGER" == "apt" ]]; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    $INSTALL_CMD nodejs
elif [[ "$PKG_MANAGER" == "yum" ]]; then
    curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
    $INSTALL_CMD nodejs npm
else
    $INSTALL_CMD nodejs npm
fi

# Update npm to latest
npm install -g npm@latest

log_info "Installing Rust (latest stable)..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
rustup update

log_info "Installing TypeScript globally..."
npm install -g typescript ts-node @types/node

log_success "All programming languages installed"

# =============================================================================
# PACKAGE MANAGERS AND BUILD TOOLS
# =============================================================================

log_info "Installing uv (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | sh

log_info "Installing additional build tools..."
if [[ "$PKG_MANAGER" == "apt" ]]; then
    $INSTALL_CMD make cmake clang pkg-config libssl-dev
elif [[ "$PKG_MANAGER" == "yum" ]]; then
    $INSTALL_CMD make cmake clang pkgconfig openssl-devel
else
    $INSTALL_CMD make cmake clang
fi

log_success "Package managers and build tools installed"

# =============================================================================
# GITHUB CLI AND SSH SETUP
# =============================================================================

log_info "Installing GitHub CLI..."
if [[ "$PKG_MANAGER" == "apt" ]]; then
    # Add GitHub CLI repository
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    $INSTALL_CMD gh
else
    # Fallback: install from releases
    GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/v//')
    curl -LO "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz"
    tar -xzf "gh_${GH_VERSION}_linux_amd64.tar.gz"
    sudo mv "gh_${GH_VERSION}_linux_amd64/bin/gh" /usr/local/bin/
    rm -rf "gh_${GH_VERSION}_linux_amd64" "gh_${GH_VERSION}_linux_amd64.tar.gz"
fi

log_info "Setting up SSH directory..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

log_success "GitHub CLI installed"

# =============================================================================
# AI CODE ASSISTANTS
# =============================================================================

log_info "Installing AI code assistants..."

# Install Aider (AI pair programmer)
python -m pip install --user aider-chat

# Install other AI tools
npm install -g @githubnext/github-copilot-cli 2>/dev/null || log_warning "GitHub Copilot CLI not available"

log_success "AI code assistants installed"

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

log_info "Installing additional development tools..."

# Language servers and formatters
npm install -g pyright prettier eslint typescript-language-server

# Python tools
python -m pip install --user black isort flake8 mypy pylsp rope

# Rust tools
cargo install ripgrep fd-find bat exa

# Database tools
if [[ "$PKG_MANAGER" == "apt" ]]; then
    $INSTALL_CMD sqlite3
else
    $INSTALL_CMD sqlite
fi

# Install neofetch for system info
if [[ "$PKG_MANAGER" == "apt" ]]; then
    $INSTALL_CMD neofetch
fi

log_success "Development tools installed"

# =============================================================================
# SHORTCUTS AND ALIASES
# =============================================================================

log_info "Creating shortcuts directory..."
mkdir -p ~/.shortcuts

# Create aliases file
log_info "Setting up aliases..."
cat >> ~/.bashrc << 'EOF'

# =============================================================================
# DEVELOPMENT ALIASES
# =============================================================================

# System shortcuts
alias ll='ls -la'
alias la='ls -la'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias h='history'
alias c='clear'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gd='git diff'
alias gb='git branch'
alias gco='git checkout'
alias glog='git log --oneline --graph'

# Development shortcuts
alias py='python'
alias pip='python -m pip'
alias node='node'
alias ts='npx ts-node'
alias rs='cargo run'
alias rb='cargo build'
alias rt='cargo test'

# Package managers
alias piu='python -m pip install --user --upgrade'
alias ni='npm install'
alias nig='npm install -g'
alias nr='npm run'
alias nt='npm test'
alias ns='npm start'

# System maintenance
alias cleanup='bash <(curl -s https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/cleanup-linux.sh)'
alias sysinfo='neofetch 2>/dev/null || (echo "System Info:"; uname -a; echo ""; df -h)'
alias ports='netstat -tuln 2>/dev/null || ss -tuln'

# AI assistants
alias ask='aider'
alias copilot='github-copilot-cli'

# Useful shortcuts
alias weather='curl wttr.in'
alias myip='curl ifconfig.me'
alias serve='python -m http.server 8000'
alias tree='tree -C'
alias cat='bat --style=plain 2>/dev/null || cat'
alias ls='exa --color=always 2>/dev/null || ls --color=auto'

# PATH additions
export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/go/bin:$PATH"

EOF

# Create cleanup script for Linux
cat > ~/.shortcuts/cleanup-linux.sh << 'EOF'
#!/bin/bash

echo "🧹 Starting Linux cleanup..."

# Check initial disk usage
echo "📊 Initial disk usage:"
df -h ~

echo ""
echo "🗑️  Cleaning package manager cache..."
if command -v apt &> /dev/null; then
    sudo apt autoremove -y
    sudo apt autoclean
elif command -v yum &> /dev/null; then
    sudo yum autoremove -y
    sudo yum clean all
fi

echo "🗑️  Clearing temporary files..."
find /tmp -type f -delete 2>/dev/null || true
find ~/.cache -type f -delete 2>/dev/null || true
rm -rf ~/.npm/_cacache 2>/dev/null || true

echo "🗑️  Cleaning log files..."
find ~/.local/share -name "*.log" -type f -delete 2>/dev/null || true
find ~ -name "*.log" -maxdepth 2 -type f -delete 2>/dev/null || true

echo "🗑️  Cleaning build artifacts..."
find ~ -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
find ~ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find ~ -name "*.pyc" -type f -delete 2>/dev/null || true
find ~ -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

echo "🗑️  Cleaning editor temporary files..."
find ~ -name "*~" -type f -delete 2>/dev/null || true
find ~ -name "*.swp" -type f -delete 2>/dev/null || true
find ~ -name "*.tmp" -type f -delete 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo "📊 Final disk usage:"
df -h ~

echo ""
echo "💾 Cleanup finished on $(date)"
EOF

chmod +x ~/.shortcuts/cleanup-linux.sh

# Create other shortcut scripts (same as before but Linux compatible)
cat > ~/.shortcuts/init-project.sh << 'EOF'
#!/bin/bash
PROJECT_NAME="${1:-my-project}"
PROJECT_TYPE="${2:-node}"

case $PROJECT_TYPE in
    "node"|"js"|"ts")
        mkdir -p "$PROJECT_NAME"
        cd "$PROJECT_NAME"
        npm init -y
        npm install -D typescript @types/node ts-node
        echo "console.log('Hello, World!');" > index.ts
        ;;
    "python"|"py")
        mkdir -p "$PROJECT_NAME"
        cd "$PROJECT_NAME"
        python -m venv venv
        echo "print('Hello, World!')" > main.py
        echo "venv/" > .gitignore
        ;;
    "rust"|"rs")
        cargo new "$PROJECT_NAME"
        cd "$PROJECT_NAME"
        ;;
    *)
        mkdir -p "$PROJECT_NAME"
        cd "$PROJECT_NAME"
        git init
        echo "# $PROJECT_NAME" > README.md
        ;;
esac

git init 2>/dev/null || true
echo "🚀 Project '$PROJECT_NAME' initialized with type '$PROJECT_TYPE'"
EOF

chmod +x ~/.shortcuts/init-project.sh

cat > ~/.shortcuts/github-setup.sh << 'EOF'
#!/bin/bash
echo "🔐 Setting up GitHub authentication..."
echo ""
echo "1. First, authenticate with GitHub CLI:"
echo "   gh auth login"
echo ""
echo "2. Generate SSH key (if needed):"
echo "   ssh-keygen -t ed25519 -C 'your_email@example.com'"
echo ""
echo "3. Add SSH key to GitHub:"
echo "   gh ssh-key add ~/.ssh/id_ed25519.pub --title 'Codespace Key'"
echo ""
echo "4. Test SSH connection:"
echo "   ssh -T git@github.com"
echo ""
read -p "Run GitHub CLI authentication now? (y/n): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh auth login
fi
EOF

chmod +x ~/.shortcuts/github-setup.sh

log_success "Aliases and shortcuts created"

# =============================================================================
# FINAL SETUP
# =============================================================================

log_info "Finalizing setup..."

# Source the new bashrc
source ~/.bashrc 2>/dev/null || true

# Create welcome message
cat > ~/.welcome.sh << 'EOF'
#!/bin/bash
echo "🎉 Welcome to your Linux development environment!"
echo ""
echo "🚀 Available shortcuts:"
echo "  cleanup          - Clean system caches"
echo "  sysinfo          - Show system information"
echo "  init-project     - Initialize new project"
echo "  github-setup     - Setup GitHub authentication"
echo ""
echo "🛠️  Languages installed:"
echo "  Python $(python --version 2>&1 | cut -d' ' -f2) | Node.js $(node --version) | Rust $(rustc --version | cut -d' ' -f2)"
echo ""
echo "💡 Quick start:"
echo "  gh auth login    - Authenticate with GitHub"
echo "  init-project myapp node  - Create Node.js project"
echo "  aider           - Start AI pair programming"
echo ""
EOF

chmod +x ~/.welcome.sh

# Add welcome message to bashrc
echo "" >> ~/.bashrc
echo "# Welcome message" >> ~/.bashrc
echo "~/.welcome.sh" >> ~/.bashrc

log_success "Setup completed successfully!"

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Run: gh auth login (to setup GitHub)"
echo "3. Run: sysinfo (to see installed tools)"
echo "4. Run: init-project myapp (to create a project)"
echo ""
echo "🔧 All shortcuts are available in ~/.shortcuts/"
echo "💡 Type 'alias' to see all available shortcuts"
echo ""
#!/bin/bash

# 🚀 Complete Development Environment Setup for Termux/Codespace
# Sets up languages, tools, AI assistants, and useful shortcuts

set -e  # Exit on any error

echo "🚀 Starting complete development environment setup..."
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

# =============================================================================
# SYSTEM UPDATE AND BASIC TOOLS
# =============================================================================

log_info "Updating system packages..."
pkg update -y && pkg upgrade -y

log_info "Installing essential tools..."
pkg install -y curl wget git vim nano htop tree jq unzip zip tar gzip

log_success "System update and basic tools installed"

# =============================================================================
# PROGRAMMING LANGUAGES
# =============================================================================

log_info "Installing Python (latest stable)..."
pkg install -y python python-pip
python -m pip install --upgrade pip

log_info "Installing Node.js and npm (latest LTS)..."
pkg install -y nodejs npm
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
source ~/.local/bin/env

log_info "Installing additional build tools..."
pkg install -y make cmake clang

log_success "Package managers and build tools installed"

# =============================================================================
# GITHUB CLI AND SSH SETUP
# =============================================================================

log_info "Installing GitHub CLI..."
pkg install -y gh

log_info "Setting up SSH directory..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh

log_info "GitHub CLI installed. Run 'gh auth login' to authenticate."

# =============================================================================
# AI CODE ASSISTANTS
# =============================================================================

log_info "Installing AI code assistants..."

# Install Claude CLI (if available)
npm install -g @anthropic-ai/claude-cli 2>/dev/null || log_warning "Claude CLI not available via npm"

# Install GitHub Copilot CLI
npm install -g @githubnext/github-copilot-cli 2>/dev/null || log_warning "GitHub Copilot CLI installation failed"

# Install Aider (AI pair programmer)
python -m pip install aider-chat

# Install CodeGPT CLI
npm install -g code-gpt 2>/dev/null || log_warning "CodeGPT CLI installation failed"

log_success "AI code assistants installed"

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

log_info "Installing additional development tools..."

# Language servers and formatters
npm install -g pyright prettier eslint
python -m pip install black isort flake8 mypy
cargo install ripgrep fd-find bat exa

# Database tools
pkg install -y sqlite

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
alias piu='python -m pip install --upgrade'
alias ni='npm install'
alias nig='npm install -g'
alias nr='npm run'
alias nt='npm test'
alias ns='npm start'

# System maintenance
alias cleanup='~/cleanup-termux.sh'
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

# Create individual shortcut scripts
log_info "Creating shortcut scripts..."

# System setup script
cat > ~/.shortcuts/dev-setup.sh << 'EOF'
#!/bin/bash
~/dev-setup.sh "$@"
EOF

# Cleanup script
cat > ~/.shortcuts/cleanup-termux.sh << 'EOF'
#!/bin/bash
~/cleanup-termux.sh "$@"
EOF

# Quick project init
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

# GitHub setup helper
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
echo "   gh ssh-key add ~/.ssh/id_ed25519.pub --title 'Termux Key'"
echo ""
echo "4. Test SSH connection:"
echo "   ssh -T git@github.com"
echo ""
read -p "Run GitHub CLI authentication now? (y/n): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh auth login
fi
EOF

# System info script
cat > ~/.shortcuts/sysinfo.sh << 'EOF'
#!/bin/bash
echo "📊 System Information"
echo "===================="
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo ""
echo "📁 Disk Usage:"
df -h ~ | tail -1
echo ""
echo "💾 Memory:"
free -h 2>/dev/null || echo "Memory info not available"
echo ""
echo "🔧 Installed Languages:"
echo "Python: $(python --version 2>&1 | head -1)"
echo "Node.js: $(node --version 2>&1)"
echo "Rust: $(rustc --version 2>&1)"
echo "TypeScript: $(tsc --version 2>&1)"
echo ""
echo "📦 Package Managers:"
echo "pip: $(pip --version 2>&1 | cut -d' ' -f2)"
echo "npm: $(npm --version 2>&1)"
echo "cargo: $(cargo --version 2>&1 | cut -d' ' -f2)"
echo "uv: $(uv --version 2>&1 || echo 'Not installed')"
EOF

# Make all shortcuts executable
chmod +x ~/.shortcuts/*.sh

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
echo "🎉 Welcome to your development environment!"
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
echo "🔧 All shortcuts are available in ~/.shortcuts/ for Termux Widget"
echo "💡 Type 'alias' to see all available shortcuts"
echo ""
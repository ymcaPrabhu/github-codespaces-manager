#!/bin/bash

# 🚀 Quick fix for ymcaPrabhu/module1 codespace creation issue
# This script specifically handles the branch detection issue for your repository

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🔧 Fixing ymcaPrabhu/module1 codespace creation..."
echo ""

# Check authentication
if ! gh auth status &>/dev/null; then
    log_error "GitHub CLI not authenticated. Run: gh auth login"
    exit 1
fi

REPO="ymcaPrabhu/module1"

# Check if repo exists
if ! gh repo view "$REPO" &>/dev/null; then
    log_error "Repository $REPO does not exist or is not accessible"
    exit 1
fi

# Get default branch
log_info "Detecting default branch..."
default_branch=$(gh repo view "$REPO" --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null)

if [[ -z "$default_branch" || "$default_branch" == "null" ]]; then
    log_warning "Could not detect default branch. Trying common branch names..."
    for branch in main master develop; do
        if gh api "repos/$REPO/branches/$branch" &>/dev/null; then
            default_branch="$branch"
            break
        fi
    done
fi

if [[ -z "$default_branch" ]]; then
    log_error "No valid branch found. Repository may be empty."
    log_info "Creating initial commit..."

    # Create temporary directory and initialize repo
    temp_dir=$(mktemp -d)
    cd "$temp_dir"
    git clone "https://github.com/$REPO.git"
    cd module1

    # Create initial files if repo is empty
    if [[ ! -f README.md ]]; then
        echo "# module1" > README.md
    fi

    # Check if we have any files to commit
    if [[ -z "$(git ls-files)" ]]; then
        git add README.md
        git commit -m "Initial commit"
        git push origin main
        default_branch="main"
        log_success "Repository initialized with initial commit!"
    fi

    cd ~
    rm -rf "$temp_dir"
fi

if [[ -n "$default_branch" ]]; then
    log_success "Using branch: $default_branch"
    log_info "Creating codespace for $REPO..."

    if gh codespace create --repo "$REPO" --branch "$default_branch"; then
        log_success "Codespace created successfully!"
        echo ""
        log_info "Available codespaces:"
        gh codespace list
        echo ""
        log_info "To connect to your codespace, run: setupdev"
    else
        log_error "Failed to create codespace"
        exit 1
    fi
else
    log_error "Could not determine a valid branch for codespace creation"
    exit 1
fi
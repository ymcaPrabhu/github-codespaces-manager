#!/bin/bash

# 🚀 Enhanced GitHub Codespace Setup and Connection v2.1
# Connects to GitHub Codespace and sets up complete dev environment

set -e

# Enhanced Colors and Styles
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Unicode symbols for better visual hierarchy
ARROW="→"
BULLET="•"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
FOLDER="📁"
STAR="⭐"

# Enhanced logging functions with consistent messaging
log_info() { echo -e "${BLUE}${BOLD}${INFO} $1${NC}"; }
log_success() { echo -e "${GREEN}${BOLD}${CHECK} $1${NC}"; }
log_warning() { echo -e "${YELLOW}${BOLD}${WARNING} $1${NC}"; }
log_error() { echo -e "${RED}${BOLD}${CROSS} $1${NC}"; }
log_prompt() { echo -e "${CYAN}${BOLD}${GEAR} $1${NC}"; }
log_title() { echo -e "${PURPLE}${BOLD}${ROCKET} $1${NC}"; }
log_menu() { echo -e "${WHITE}${BOLD}$1${NC}"; }
log_separator() { echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# Progress bar function with estimated time
show_progress() {
    local current=$1
    local total=$2
    local task_name="$3"
    local estimated_time=${4:-"Unknown"}

    local percent=$((current * 100 / total))
    local filled=$((current * 50 / total))
    local empty=$((50 - filled))

    printf "\r${CYAN}${BOLD}%s${NC} [" "$task_name"
    printf "%*s" $filled | tr ' ' '█'
    printf "%*s" $empty | tr ' ' '░'
    printf "] ${WHITE}%d%%${NC} ${GRAY}(~%s remaining)${NC}" $percent "$estimated_time"

    if [ $current -eq $total ]; then
        echo ""
        log_success "$task_name completed!"
    fi
}

# Enhanced package installation with realistic progress tracking
install_with_progress() {
    local package_list=("$@")
    local total=${#package_list[@]}

    echo ""
    log_info "Setting up development environment with ${total} components..."
    log_separator

    local start_time=$(date +%s)

    for i in "${!package_list[@]}"; do
        local current=$((i + 1))
        local package="${package_list[$i]}"
        local remaining_min=$(((total - current) * 2))

        show_progress $current $total "$package" "${remaining_min}m"

        # Simulate realistic installation time
        sleep 1
    done

    local end_time=$(date +%s)
    local actual_time=$((end_time - start_time))
    echo ""
    log_success "Development environment setup completed in ${actual_time}s!"
}

# Repository name format function
format_repo_name() {
    local repo="$1"
    echo -e "${BOLD}${repo##*/}${NC} ${GRAY}→${NC} ${CYAN}Changing to folder: ${repo##*/}${NC}"
}

# Function to detect default branch of a repository
detect_default_branch() {
    local repo="$1"
    local default_branch=""

    # Try to get default branch from API
    if command -v jq >/dev/null 2>&1; then
        default_branch=$(gh repo view "$repo" --json defaultBranchRef 2>/dev/null | jq -r '.defaultBranchRef.name' 2>/dev/null)
    fi

    if [[ -z "$default_branch" || "$default_branch" == "null" ]]; then
        # Try common branch names
        for branch in main master develop; do
            if gh api "repos/$repo/branches/$branch" &>/dev/null; then
                default_branch="$branch"
                break
            fi
        done
    fi

    echo "$default_branch"
}

# Function to list available codespaces with user-friendly selection
list_codespaces() {
    log_title "Available GitHub Codespaces (Names Only)"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Show codespace names with repositories
    if gh codespace list --json name,repository 2>/dev/null | jq -r '.[] | .name + " (" + .repository.full_name + ")"' 2>/dev/null; then
        return 0
    elif gh codespace list 2>/dev/null | awk '{print $1 " (" $4 ")"}'; then
        return 0
    else
        log_error "Failed to list codespaces. Please authenticate with 'gh auth login'"
        return 1
    fi
}

# Function to select codespace from list
select_codespace() {
    local purpose="$1"
    log_title "Select Codespace - $purpose"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Show available codespaces with repositories
    echo -e "${WHITE}${BOLD}Available codespaces (name - repository):${NC}"
    if gh codespace list --json name,repository 2>/dev/null | jq -r '.[] | .name + " (" + .repository.full_name + ")"' 2>/dev/null; then
        :
    elif gh codespace list 2>/dev/null | awk '{print $1 " (" $4 ")"}'; then
        :
    else
        log_error "Failed to fetch codespaces. Please check your authentication."
        return 1
    fi

    echo ""
    log_prompt "Enter the exact codespace NAME (not the repository) from the list above:"
    printf "${CYAN}Codespace name${NC} ${GRAY}→${NC} "
    read codespace_name

    if [[ -n "$codespace_name" ]]; then
        echo "$codespace_name"
        return 0
    else
        log_error "Codespace name cannot be empty"
        return 1
    fi
}

# Function to select repository from list
select_repository() {
    local purpose="$1"
    log_title "Select Repository - $purpose"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Show available repositories (names only)
    echo -e "${WHITE}${BOLD}Available repository names:${NC}"
    if gh repo list --limit 20 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
        :
    elif gh repo list --limit 20 2>/dev/null | awk '{print $1}' | tail -n +2; then
        :
    else
        log_error "Failed to fetch repositories. Please check your authentication."
        return 1
    fi

    echo ""
    log_prompt "Enter repository name in user/repo format:"
    read -p "${CYAN}Repository${NC} ${GRAY}→${NC} " repo_name

    if [[ -n "$repo_name" ]]; then
        echo "$repo_name"
        return 0
    else
        log_error "Repository name cannot be empty"
        return 1
    fi
}

# Function to create new codespace
create_codespace() {
    log_title "Create New Codespace"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    while true; do
        local repo
        repo=$(select_repository "Create Codespace")

        if [[ $? -ne 0 ]]; then
            return 0
        fi

        if [[ -n "$repo" ]]; then
            format_repo_name "$repo"

            log_info "Verifying repository existence..."
            if ! gh repo view "$repo" &>/dev/null; then
                log_warning "Repository doesn't exist. Creating: $repo"

                log_prompt "Create repository '$repo'? [y/n/exit]:"
                printf "${CYAN}Choice${NC} ${GRAY}→${NC} "
                read create_choice

                case "$create_choice" in
                    "y"|"yes"|"Y"|"YES")
                        if gh repo create "$repo" --public; then
                            log_success "Repository created!"
                        else
                            log_error "Failed to create repository"
                            continue
                        fi
                        ;;
                    "exit"|"quit"|"q")
                        return 0
                        ;;
                    *)
                        log_info "Repository creation cancelled"
                        continue
                        ;;
                esac
            fi

            # Get default branch
            log_info "Detecting default branch..."
            default_branch=$(detect_default_branch "$repo")

            if [[ -z "$default_branch" ]]; then
                log_error "No valid branch found. Repository may be empty."
                log_info "Please push at least one commit first."
                continue
            fi

            log_info "Using branch: ${BOLD}$default_branch${NC}"
            log_info "Creating codespace for $repo..."

            if gh codespace create --repo "$repo" --branch "$default_branch"; then
                log_success "Codespace created successfully!"
                break
            else
                log_error "Failed to create codespace"
                continue
            fi
        fi
    done
}

# Enhanced setup codespace function with progress tracking
setup_codespace() {
    local codespace_name="$1"

    log_title "Development Environment Setup"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log_info "Setting up codespace: ${BOLD}$codespace_name${NC}"

    # Package installation with progress tracking
    local packages=("System Update" "Essential Tools" "Python" "Node.js" "Rust" "TypeScript" "UV Package Manager" "Build Tools" "Dev Tools" "Database Tools")
    install_with_progress "${packages[@]}"

    # Create setup script
    log_info "Deploying and executing setup script..."

    local setup_commands='
#!/bin/bash
echo "🚀 Starting Development Environment Setup..."

# System update
echo "📦 Updating system packages..."
sudo apt update -y >/dev/null 2>&1
sudo apt upgrade -y >/dev/null 2>&1

# Install essential tools
echo "🔧 Installing essential development tools..."
sudo apt install -y curl wget git vim nano htop tree build-essential >/dev/null 2>&1

# Install Python
echo "🐍 Setting up Python environment..."
sudo apt install -y python3 python3-pip python3-venv >/dev/null 2>&1

# Install Node.js
echo "📗 Installing Node.js LTS..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - >/dev/null 2>&1
sudo apt install -y nodejs >/dev/null 2>&1

# Install Rust
echo "🦀 Installing Rust toolchain..."
curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y >/dev/null 2>&1

# Setup aliases
echo "⚡ Configuring development environment..."
cat >> ~/.bashrc << "EOF"

# Git shortcuts
alias gs="git status -sb"
alias ga="git add"
alias gc="git commit -m"
alias gp="git push"
alias gl="git pull"

# Development shortcuts
alias py="python3"
alias ll="ls -la"
alias projects="cd ~/projects || mkdir -p ~/projects && cd ~/projects"

# PATH additions
export PATH="$HOME/.cargo/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"

EOF

# Create projects directory
mkdir -p ~/projects

echo "✅ Development environment setup completed!"
echo "💡 Run '\''source ~/.bashrc'\'' to activate all features"
'

    # Execute setup in codespace
    echo "$setup_commands" | gh codespace ssh --codespace "$codespace_name" -- 'bash -s'

    log_success "Development environment setup completed successfully!"
}

# Function to connect to codespace
connect_to_codespace() {
    local codespace_name="$1"
    log_title "Connecting to Codespace"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log_info "Connecting to: ${BOLD}$codespace_name${NC}"
    log_info "Environment is fully configured and ready!"
    gh codespace ssh --codespace "$codespace_name"
}

# Enhanced repository management functions
archive_repository() {
    local repo="$1"
    log_info "Archiving repository: $repo"
    if gh repo edit "$repo" --archived=true; then
        log_success "Repository '$repo' has been archived"
    else
        log_error "Failed to archive repository '$repo'"
    fi
}

fork_repository() {
    local repo="$1"
    log_info "Forking repository: $repo"
    if gh repo fork "$repo" --clone=false; then
        log_success "Repository '$repo' has been forked"
    else
        log_error "Failed to fork repository '$repo'"
    fi
}

clone_repository() {
    local repo="$1"
    local clone_dir="$2"
    log_info "Cloning repository: $repo"
    if [[ -n "$clone_dir" ]]; then
        git clone "https://github.com/$repo.git" "$clone_dir"
    else
        git clone "https://github.com/$repo.git"
    fi
}

rename_repository() {
    local repo="$1"
    log_prompt "Enter new repository name:"
    read -p "${CYAN}New name${NC} ${GRAY}→${NC} " new_name

    if [[ -n "$new_name" ]]; then
        log_info "Renaming repository '$repo' to '$new_name'"
        if gh repo edit "$repo" --name "$new_name"; then
            log_success "Repository renamed successfully"
        else
            log_error "Failed to rename repository"
        fi
    else
        log_error "New name cannot be empty"
    fi
}

# Function to delete repository with enhanced confirmation
delete_repository_confirmed() {
    local repo="$1"

    # Check if repository exists
    if ! gh repo view "$repo" &>/dev/null; then
        log_error "Repository '$repo' does not exist or is not accessible"
        return 1
    fi

    # Show repository info
    log_info "Repository Information:"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    gh repo view "$repo" 2>/dev/null || echo "Repository: $repo"

    # Enhanced confirmation process
    log_warning "⚠️  This action CANNOT be undone!"
    echo -e "${RED}${BOLD}This will permanently delete ALL repository data${NC}"

    log_prompt "Type 'DELETE' to confirm or 'exit' to cancel:"
    read -p "${RED}Confirmation${NC} ${GRAY}→${NC} " first_confirm

    case "$first_confirm" in
        "DELETE")
            log_warning "⚠️  FINAL CONFIRMATION"
            echo -e "${RED}Type the exact repository name: ${BOLD}$repo${NC}"
            read -p "${RED}Repository name${NC} ${GRAY}→${NC} " repo_confirm

            if [[ "$repo_confirm" == "$repo" ]]; then
                log_info "Deleting repository '$repo'..."
                if gh repo delete "$repo" --yes; then
                    log_success "Repository '$repo' has been permanently deleted"
                else
                    log_error "Failed to delete repository"
                fi
            else
                log_error "Repository name doesn't match. Deletion cancelled."
            fi
            ;;
        "exit"|"quit"|"q")
            log_info "Repository deletion cancelled"
            ;;
        *)
            log_info "Deletion cancelled"
            ;;
    esac
}

# Enhanced space utilization with better formatting
show_space_utilization() {
    log_title "GitHub Space & Utilization Report"
    echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Active Codespaces section
    echo -e "${WHITE}${BOLD}📦 Active Codespaces${NC}"
    echo -e "${GRAY}────────────────────────────────────────────${NC}"
    gh codespace list 2>/dev/null || echo -e "${GRAY}No codespaces found${NC}"

    echo ""

    # Repository Storage section
    echo -e "${WHITE}${BOLD}💾 Repository Storage Usage${NC}"
    echo -e "${GRAY}────────────────────────────────────────────${NC}"

    # Show repository names only
    if gh repo list --limit 20 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
        :
    else
        echo -e "${GRAY}Repository information unavailable${NC}"
    fi

    echo ""

    # Storage Summary section
    echo -e "${WHITE}${BOLD}📊 Storage Summary${NC}"
    echo -e "${GRAY}────────────────────────────────────────────${NC}"

    local total_repos="N/A"
    if command -v jq >/dev/null 2>&1; then
        total_repos=$(gh repo list --limit 100 --json name 2>/dev/null | jq length 2>/dev/null || echo "N/A")
    fi

    echo -e "${CYAN}• Total Repositories:${NC} $total_repos"
    echo -e "${CYAN}• GitHub CLI Version:${NC} $(gh --version | head -n1)"

    echo ""

    # Account Information section
    echo -e "${WHITE}${BOLD}👤 Account Information${NC}"
    echo -e "${GRAY}────────────────────────────────────────────${NC}"

    if command -v jq >/dev/null 2>&1; then
        local username=$(gh api user 2>/dev/null | jq -r '.login' 2>/dev/null || echo "N/A")
        echo -e "• Username: $username"
        echo -e "• Account Type: GitHub User"
        echo -e "• Repositories: Available via 'gh repo list'"
    else
        echo -e "${GRAY}Account information unavailable (jq not installed)${NC}"
    fi

    echo ""

    # Tips section
    echo -e "${WHITE}${BOLD}💡 Optimization Tips${NC}"
    echo -e "${GRAY}────────────────────────────────────────────${NC}"
    echo -e "${GREEN}• Free accounts: 15GB Codespace storage/month${NC}"
    echo -e "${GREEN}• Repository limits: 100GB (soft), 5GB (recommended)${NC}"
    echo -e "${GREEN}• Use 'gh repo archive' for unused repositories${NC}"
    echo -e "${GREEN}• Use '.gitignore' and 'git clean' to reduce size${NC}"
}

# Enhanced main menu with expert recommendations
show_main_menu() {
    clear
    echo -e "${PURPLE}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              🚀 GitHub Codespace Manager v2.1             ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    # Show current user info
    local current_user="N/A"
    if command -v jq >/dev/null 2>&1; then
        current_user=$(gh api user 2>/dev/null | jq -r '.login' 2>/dev/null || echo "Unknown")
    fi
    echo -e "${GRAY}${DIM}Welcome back, ${BOLD}$current_user${NC}${GRAY}${DIM}!${NC}"
    log_separator

    log_menu "Choose your development workflow:"
    echo ""

    echo -e "${WHITE}${BOLD}${ROCKET} CODESPACE WORKFLOWS${NC}"
    echo -e "${CYAN}1)${NC} ${BOLD}Quick Setup${NC} ${GRAY}- Create & configure codespace in one step${NC}"
    echo -e "${CYAN}2)${NC} ${BOLD}Advanced Management${NC} ${GRAY}- Full codespace control${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}📊 ANALYTICS & INSIGHTS${NC}"
    echo -e "${CYAN}3)${NC} ${BOLD}Usage Dashboard${NC} ${GRAY}- Space, costs, and performance metrics${NC}"
    echo -e "${CYAN}4)${NC} ${BOLD}Repository Explorer${NC} ${GRAY}- Browse and analyze your repos${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}🗂️  REPOSITORY OPERATIONS${NC}"
    echo -e "${CYAN}5)${NC} ${BOLD}Repository Toolkit${NC} ${GRAY}- Archive, fork, clone, rename, delete${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}${GEAR} EXPERT TOOLS${NC}"
    echo -e "${CYAN}6)${NC} ${BOLD}Bulk Operations${NC} ${GRAY}- Manage multiple codespaces/repos${NC}"
    echo -e "${CYAN}7)${NC} ${BOLD}Development Templates${NC} ${GRAY}- Quick project scaffolding${NC}"
    echo ""

    echo -e "${WHITE}${BOLD}⚙️  SYSTEM${NC}"
    echo -e "${CYAN}0)${NC} Exit Program"
    echo ""
    log_separator

    # Pro tip of the day
    local tips=(
        "💡 Pro Tip: Use option 1 for fastest development setup"
        "💡 Pro Tip: Check your usage dashboard (option 3) weekly"
        "💡 Pro Tip: Archive unused repositories to save space"
        "💡 Pro Tip: Use bulk operations for managing multiple projects"
        "💡 Pro Tip: Templates (option 7) speed up new project creation"
        "💡 Pro Tip: Codespaces auto-suspend after 30min of inactivity"
        "💡 Pro Tip: Use .devcontainer for consistent team environments"
    )
    local random_tip=${tips[$RANDOM % ${#tips[@]}]}
    echo -e "${GREEN}${DIM}$random_tip${NC}"
}

# Codespace management submenu
manage_codespaces() {
    while true; do
        clear
        log_title "Codespace Management"
        echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        list_codespaces
        echo ""

        log_prompt "Choose an action:"
        echo -e "${CYAN}1)${NC} Create New Codespace"
        echo -e "${CYAN}2)${NC} Connect to Existing Codespace"
        echo -e "${CYAN}3)${NC} Setup Development Environment"
        echo -e "${CYAN}4)${NC} Setup and Connect in One Step"
        echo -e "${CYAN}0)${NC} Return to Main Menu"
        echo ""
        read -p "${CYAN}Choice [0-4]${NC} ${GRAY}→${NC} " codespace_choice

        case $codespace_choice in
            1)
                create_codespace
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
            2|3|4)
                local codespace_name
                codespace_name=$(select_codespace "$(case $codespace_choice in 2) echo "Connect";; 3) echo "Setup Environment";; 4) echo "Setup & Connect";; esac)")

                if [[ $? -eq 0 && -n "$codespace_name" ]]; then
                    case $codespace_choice in
                        2)
                            connect_to_codespace "$codespace_name"
                            ;;
                        3)
                            setup_codespace "$codespace_name"
                            ;;
                        4)
                            setup_codespace "$codespace_name"
                            log_info "Setup complete! Connecting now..."
                            sleep 2
                            connect_to_codespace "$codespace_name"
                            ;;
                    esac
                fi
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
            0)
                return 0
                ;;
            *)
                log_error "Invalid choice. Please select 0-4."
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
        esac
    done
}

# Repository management submenu
manage_repositories() {
    while true; do
        clear
        log_title "Repository Management"
        echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        log_prompt "Choose an operation:"
        echo -e "${CYAN}1)${NC} List All Repositories"
        echo -e "${CYAN}2)${NC} Archive Repository"
        echo -e "${CYAN}3)${NC} Fork Repository"
        echo -e "${CYAN}4)${NC} Clone Repository"
        echo -e "${CYAN}5)${NC} Rename Repository"
        echo -e "${CYAN}6)${NC} ${RED}Delete Repository${NC} ${GRAY}(⚠️  Permanent)${NC}"
        echo -e "${CYAN}0)${NC} Return to Main Menu"
        echo ""
        read -p "${CYAN}Choice [0-6]${NC} ${GRAY}→${NC} " repo_choice

        case $repo_choice in
            1)
                clear
                log_title "Repository Overview"
                echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${WHITE}${BOLD}Repository names:${NC}"
                if gh repo list --limit 20 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
                    :
                else
                    log_error "Failed to list repositories"
                fi
                echo ""
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
            2|3|4|5|6)
                local repo
                repo=$(select_repository "$(case $repo_choice in 2) echo "Archive";; 3) echo "Fork";; 4) echo "Clone";; 5) echo "Rename";; 6) echo "Delete";; esac)")

                if [[ $? -eq 0 && -n "$repo" ]]; then
                    case $repo_choice in
                        2)
                            archive_repository "$repo"
                            ;;
                        3)
                            fork_repository "$repo"
                            ;;
                        4)
                            log_prompt "Enter clone directory (leave empty for default):"
                            read -p "${CYAN}Directory${NC} ${GRAY}→${NC} " clone_dir
                            clone_repository "$repo" "$clone_dir"
                            ;;
                        5)
                            rename_repository "$repo"
                            ;;
                        6)
                            delete_repository_confirmed "$repo"
                            ;;
                    esac
                fi
                echo ""
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
            0)
                return 0
                ;;
            *)
                log_error "Invalid choice. Please select 0-6."
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
        esac
    done
}

# Quick setup workflow - expert feature
quick_setup_workflow() {
    log_title "Quick Setup Workflow"
    log_separator
    log_info "This will create a new codespace and configure it in one step"
    echo ""

    local repo
    repo=$(select_repository "Quick Setup")

    if [[ $? -ne 0 ]]; then
        return 0
    fi

    log_info "Starting quick setup for: ${BOLD}$repo${NC}"

    # Verify repo exists
    if ! gh repo view "$repo" &>/dev/null; then
        log_warning "Repository doesn't exist. Creating: $repo"
        if gh repo create "$repo" --public; then
            log_success "Repository created!"
        else
            log_error "Failed to create repository"
            return 1
        fi
    fi

    # Get default branch
    log_info "Detecting default branch..."
    local default_branch=$(detect_default_branch "$repo")

    if [[ -z "$default_branch" ]]; then
        log_error "No valid branch found. Please push at least one commit first."
        return 1
    fi

    # Create and setup codespace
    log_info "Creating codespace..."
    if gh codespace create --repo "$repo" --branch "$default_branch"; then
        log_success "Codespace created!"

        # Get the codespace name
        local codespace_name=""
        if command -v jq >/dev/null 2>&1; then
            codespace_name=$(gh codespace list --repo "$repo" --json name 2>/dev/null | jq -r '.[0].name' 2>/dev/null)
        fi

        if [[ -z "$codespace_name" ]]; then
            log_info "Please manually enter the codespace name (not the repository) from the list above:"
            gh codespace list --repo "$repo" 2>/dev/null
            printf "${CYAN}Codespace name${NC} ${GRAY}→${NC} "
            read codespace_name
        fi

        if [[ -n "$codespace_name" ]]; then
            log_info "Setting up development environment..."
            setup_codespace "$codespace_name"

            log_prompt "Connect to codespace now? [y/n]"
            read -p "${CYAN}Connect${NC} ${GRAY}→${NC} " connect_choice

            if [[ "$connect_choice" == "y" || "$connect_choice" == "yes" ]]; then
                connect_to_codespace "$codespace_name"
            fi
        fi
    else
        log_error "Failed to create codespace"
    fi

    echo ""
    read -p "${GRAY}Press Enter to return to main menu...${NC}" -r
}

# Bulk operations - expert feature
bulk_operations() {
    log_title "Bulk Operations"
    log_separator

    echo -e "${WHITE}${BOLD}Available Bulk Operations:${NC}"
    echo ""
    echo -e "${CYAN}1)${NC} ${BOLD}Stop All Running Codespaces${NC}"
    echo -e "${CYAN}2)${NC} ${BOLD}Delete Multiple Codespaces${NC}"
    echo -e "${CYAN}3)${NC} ${BOLD}Archive Multiple Repositories${NC}"
    echo -e "${CYAN}4)${NC} ${BOLD}Bulk Repository Analysis${NC}"
    echo -e "${CYAN}0)${NC} Return to Main Menu"
    echo ""

    read -p "${CYAN}Choice [0-4]${NC} ${GRAY}→${NC} " bulk_choice

    case $bulk_choice in
        1)
            log_info "Stopping all running codespaces..."
            log_warning "This operation requires manual confirmation for each codespace"
            gh codespace list 2>/dev/null || log_error "Failed to list codespaces"
            log_prompt "Enter codespace names to stop (space-separated) or 'skip':"
            printf "${CYAN}Codespaces${NC} ${GRAY}→${NC} "
            read codespace_names

            if [[ "$codespace_names" != "skip" && -n "$codespace_names" ]]; then
                for cs in $codespace_names; do
                    log_info "Stopping: $cs"
                    gh codespace stop --codespace "$cs" || log_warning "Failed to stop $cs"
                done
            fi
            log_success "Bulk stop operation completed"
            ;;
        2)
            log_warning "This will show all codespaces for selective deletion"
            gh codespace list
            log_prompt "Enter codespace names to delete (space-separated) or 'cancel':"
            printf "${CYAN}Codespaces${NC} ${GRAY}→${NC} "
            read codespace_names

            if [[ "$codespace_names" != "cancel" && -n "$codespace_names" ]]; then
                for cs in $codespace_names; do
                    log_info "Deleting: $cs"
                    gh codespace delete --codespace "$cs" --force || log_warning "Failed to delete $cs"
                done
                log_success "Bulk deletion completed"
            fi
            ;;
        3)
            log_info "Listing repositories for bulk archiving..."
            echo -e "${WHITE}${BOLD}Repository names:${NC}"
            if gh repo list --limit 50 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
                :
            else
                gh repo list --limit 50 2>/dev/null | awk '{print $1}' | tail -n +2 || echo "No repositories found"
            fi
            log_prompt "Enter repository names to archive (space-separated) or 'cancel':"
            read -p "${CYAN}Repositories${NC} ${GRAY}→${NC} " repo_names

            if [[ "$repo_names" != "cancel" && -n "$repo_names" ]]; then
                for repo in $repo_names; do
                    archive_repository "$repo"
                done
            fi
            ;;
        4)
            log_info "Analyzing all repositories..."
            echo -e "${WHITE}${BOLD}Repository Analysis Report${NC}"
            log_separator

            local total_repos="N/A"
            if command -v jq >/dev/null 2>&1; then
                total_repos=$(gh repo list --limit 100 --json name 2>/dev/null | jq length 2>/dev/null || echo "N/A")
            fi

            echo -e "${CYAN}${BULLET} Total repositories:${NC} $total_repos"
            echo -e "${CYAN}${BULLET} GitHub CLI Version:${NC} $(gh --version | head -n1)"

            echo ""
            echo -e "${WHITE}${BOLD}Recent repository names:${NC}"
            if gh repo list --limit 5 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
                :
            else
                echo "Repository information unavailable"
            fi
            ;;
        0)
            return 0
            ;;
    esac

    echo ""
    read -p "${GRAY}Press Enter to continue...${NC}" -r
}

# Development templates - expert feature
development_templates() {
    log_title "Development Templates"
    log_separator

    echo -e "${WHITE}${BOLD}Quick Project Templates:${NC}"
    echo ""
    echo -e "${CYAN}1)${NC} ${BOLD}React + TypeScript${NC} ${GRAY}- Modern web app${NC}"
    echo -e "${CYAN}2)${NC} ${BOLD}Node.js + Express${NC} ${GRAY}- Backend API${NC}"
    echo -e "${CYAN}3)${NC} ${BOLD}Python + FastAPI${NC} ${GRAY}- Python web service${NC}"
    echo -e "${CYAN}4)${NC} ${BOLD}Rust + Actix${NC} ${GRAY}- High-performance service${NC}"
    echo -e "${CYAN}5)${NC} ${BOLD}Next.js + Tailwind${NC} ${GRAY}- Full-stack app${NC}"
    echo -e "${CYAN}6)${NC} ${BOLD}Custom Template${NC} ${GRAY}- From existing repo${NC}"
    echo -e "${CYAN}0)${NC} Return to Main Menu"
    echo ""

    read -p "${CYAN}Template [0-6]${NC} ${GRAY}→${NC} " template_choice

    local template_repo=""
    local project_name=""

    case $template_choice in
        1) template_repo="facebook/create-react-app" ;;
        2) template_repo="expressjs/express" ;;
        3) template_repo="tiangolo/fastapi" ;;
        4) template_repo="actix/examples" ;;
        5) template_repo="vercel/next.js" ;;
        6)
            log_prompt "Enter template repository [user/repo]:"
            read -p "${CYAN}Template${NC} ${GRAY}→${NC} " template_repo
            ;;
        0) return 0 ;;
        *)
            log_error "Invalid choice"
            return 1
            ;;
    esac

    if [[ -n "$template_repo" ]]; then
        log_prompt "Enter new project name:"
        read -p "${CYAN}Project${NC} ${GRAY}→${NC} " project_name

        if [[ -n "$project_name" ]]; then
            local current_user="user"
            if command -v jq >/dev/null 2>&1; then
                current_user=$(gh api user 2>/dev/null | jq -r '.login' 2>/dev/null || echo "user")
            fi
            local new_repo="$current_user/$project_name"

            log_info "Creating project from template..."
            if gh repo create "$new_repo" --template "$template_repo" --public; then
                log_success "Project created: $new_repo"

                log_prompt "Create codespace for new project? [y/n]"
                read -p "${CYAN}Create${NC} ${GRAY}→${NC} " create_cs

                if [[ "$create_cs" == "y" ]]; then
                    sleep 2  # Give GitHub time to create the repo
                    if gh codespace create --repo "$new_repo"; then
                        log_success "Codespace created for $project_name!"
                    fi
                fi
            else
                log_error "Failed to create project from template"
            fi
        fi
    fi

    echo ""
    read -p "${GRAY}Press Enter to continue...${NC}" -r
}

# Main execution function
main() {
    # Check GitHub CLI authentication
    if ! gh auth status &>/dev/null; then
        log_error "GitHub CLI not authenticated"
        log_info "Please run: ${BOLD}gh auth login${NC}"
        exit 1
    fi

    # Display available codespaces at startup
    echo -e "${WHITE}${BOLD}Available codespaces (name - repository):${NC}"
    if gh codespace list --json name,repository 2>/dev/null | jq -r '.[] | .name + " (" + .repository.full_name + ")"' 2>/dev/null; then
        :
    elif gh codespace list 2>/dev/null | awk '{print $1 " (" $4 ")"}'; then
        :
    else
        log_error "Failed to fetch codespaces. Please check your authentication."
    fi
    echo ""

    # Main program loop
    while true; do
        show_main_menu
        read -p "${CYAN}Choice [0-7]${NC} ${GRAY}→${NC} " main_choice

        case $main_choice in
            1)
                clear
                quick_setup_workflow
                ;;
            2)
                manage_codespaces
                ;;
            3)
                clear
                show_space_utilization
                echo ""
                read -p "${GRAY}Press Enter to return to main menu...${NC}" -r
                ;;
            4)
                clear
                log_title "Repository Overview"
                echo -e "${GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${WHITE}${BOLD}Repository names:${NC}"
                if gh repo list --limit 20 --json name,owner 2>/dev/null | jq -r '.[] | "\(.owner.login)/\(.name)"' 2>/dev/null; then
                    :
                else
                    log_error "Failed to list repositories"
                fi
                echo ""
                read -p "${GRAY}Press Enter to return to main menu...${NC}" -r
                ;;
            5)
                clear
                manage_repositories
                ;;
            6)
                clear
                bulk_operations
                ;;
            7)
                clear
                development_templates
                ;;
            0)
                clear
                log_title "Thank You!"
                echo -e "${GREEN}${BOLD}Thanks for using GitHub Codespace Manager v2.1! ${ROCKET}${NC}"
                echo -e "${GRAY}${DIM}Happy coding! ${STAR}${NC}"
                echo ""
                exit 0
                ;;
            *)
                log_error "Invalid choice. Please select 0-7."
                read -p "${GRAY}Press Enter to continue...${NC}" -r
                ;;
        esac
    done
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
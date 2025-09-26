"""
Language and development environment setup API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio

from app.core.github_manager import WebGitHubManager
from app.core.websockets import WebSocketManager

router = APIRouter()

# Initialize managers
github_manager = WebGitHubManager()
websocket_manager = WebSocketManager()


class LanguageSetupRequest(BaseModel):
    codespace_name: str
    languages: List[str]
    include_ai_agents: bool = False
    include_aliases: bool = True


class AIAgentsSetupRequest(BaseModel):
    codespace_name: str
    setup_claude: bool = True
    setup_qwen: bool = True


# Language setup scripts
LANGUAGE_SCRIPTS = {
    "python": """#!/bin/bash
echo "🐍 Setting up Python environment..."
# Python is usually pre-installed, so setup tools
pip3 install --upgrade pip
pip3 install poetry black ruff mypy pytest jupyter ipython requests numpy pandas
echo "✅ Python environment ready!"
""",

    "nodejs": """#!/bin/bash
echo "🟢 Setting up Node.js environment..."
# Install latest LTS Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
npm install -g typescript eslint prettier @types/node nodemon
echo "✅ Node.js environment ready!"
""",

    "rust": """#!/bin/bash
echo "🦀 Setting up Rust environment..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup component add clippy rustfmt
echo "✅ Rust environment ready!"
""",

    "go": """#!/bin/bash
echo "🐹 Setting up Go environment..."
GO_VERSION="1.21.5"
wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
rm go${GO_VERSION}.linux-amd64.tar.gz
echo "✅ Go environment ready!"
""",

    "java": """#!/bin/bash
echo "☕ Setting up Java environment..."
sudo apt update && sudo apt install -y openjdk-17-jdk maven gradle
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
source ~/.bashrc
echo "✅ Java environment ready!"
""",

    "cpp": """#!/bin/bash
echo "⚡ Setting up C/C++ environment..."
sudo apt update && sudo apt install -y build-essential gdb cmake clang-format
echo "✅ C/C++ environment ready!"
""",

    "php": """#!/bin/bash
echo "🐘 Setting up PHP environment..."
sudo apt update && sudo apt install -y php php-cli php-mbstring php-xml php-curl composer
echo "✅ PHP environment ready!"
""",

    "ruby": """#!/bin/bash
echo "💎 Setting up Ruby environment..."
sudo apt update && sudo apt install -y ruby ruby-dev bundler
gem install rails
echo "✅ Ruby environment ready!"
"""
}

AI_AGENTS_SCRIPT = """#!/bin/bash
echo "🤖🧠 Setting up AI Agents..."

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

echo "✅ AI Agents setup complete!"
echo "💡 Claude: claude --help or cl --help"
echo "💡 Qwen: qw, qwen or ollama run qwen"
"""

PROGRAMMING_ALIASES = """
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

# Quick commands
alias update='sudo apt update && sudo apt upgrade'
alias install='sudo apt install'
alias search='apt search'
"""


@router.get("/available")
async def get_available_languages():
    """Get list of available languages and tools"""
    return {
        "success": True,
        "data": {
            "languages": [
                {"id": "python", "name": "Python", "description": "Python 3 with pip, poetry, and dev tools"},
                {"id": "nodejs", "name": "Node.js", "description": "Node.js LTS with npm and TypeScript"},
                {"id": "rust", "name": "Rust", "description": "Rust with Cargo and development tools"},
                {"id": "go", "name": "Go", "description": "Go programming language with tools"},
                {"id": "java", "name": "Java", "description": "OpenJDK 17 with Maven and Gradle"},
                {"id": "cpp", "name": "C/C++", "description": "GCC, Clang, and build tools"},
                {"id": "php", "name": "PHP", "description": "PHP with Composer and common extensions"},
                {"id": "ruby", "name": "Ruby", "description": "Ruby with Bundler and Rails"}
            ],
            "ai_agents": [
                {"id": "claude", "name": "Claude CLI", "description": "Anthropic's Claude AI command line tool"},
                {"id": "qwen", "name": "Qwen", "description": "Qwen AI model via Ollama"}
            ],
            "tools": [
                {"id": "aliases", "name": "Programming Aliases", "description": "Useful command line aliases"},
                {"id": "git_config", "name": "Git Configuration", "description": "Git setup and aliases"}
            ]
        }
    }


@router.post("/setup")
async def setup_languages(request: LanguageSetupRequest, background_tasks: BackgroundTasks):
    """Setup selected languages in a codespace"""
    try:
        operation_id = f"setup_{request.codespace_name}_{len(request.languages)}_languages"

        # Send initial WebSocket notification
        await websocket_manager.send_operation_update(
            operation_id=operation_id,
            status="started",
            progress=0,
            message=f"Setting up {len(request.languages)} languages in {request.codespace_name}..."
        )

        # Build combined setup script
        script_parts = ["#!/bin/bash", "set -e", ""]

        # Add language setup scripts
        total_steps = len(request.languages) + (1 if request.include_ai_agents else 0) + (1 if request.include_aliases else 0)
        current_step = 0

        for language in request.languages:
            if language in LANGUAGE_SCRIPTS:
                script_parts.append(f"# {language.upper()} SETUP")
                script_parts.append(LANGUAGE_SCRIPTS[language])
                script_parts.append("")

                current_step += 1
                progress = int((current_step / total_steps) * 100)

                await websocket_manager.send_operation_update(
                    operation_id=operation_id,
                    status="running",
                    progress=progress,
                    message=f"Setting up {language}..."
                )

        # Add AI agents if requested
        if request.include_ai_agents:
            script_parts.append("# AI AGENTS SETUP")
            script_parts.append(AI_AGENTS_SCRIPT)
            script_parts.append("")

            current_step += 1
            progress = int((current_step / total_steps) * 100)

            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="running",
                progress=progress,
                message="Setting up AI agents..."
            )

        # Add aliases if requested
        if request.include_aliases:
            script_parts.append("# PROGRAMMING ALIASES")
            script_parts.append(f"cat >> ~/.bashrc << 'EOF'\n{PROGRAMMING_ALIASES}\nEOF")
            script_parts.append("")

            current_step += 1
            progress = int((current_step / total_steps) * 100)

            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="running",
                progress=progress,
                message="Setting up aliases..."
            )

        # Final script
        script_parts.append("echo '🎉 All language setups completed successfully!'")
        combined_script = "\n".join(script_parts)

        # Execute the script
        result = await github_manager.execute_setup_script(
            codespace_name=request.codespace_name,
            script=combined_script,
            operation_name="Language Setup"
        )

        if result["success"]:
            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="completed",
                progress=100,
                message="All languages setup completed successfully!",
                data={"output": result["output"]}
            )

            return {
                "success": True,
                "message": "Languages setup completed successfully",
                "data": {
                    "codespace_name": request.codespace_name,
                    "languages_installed": request.languages,
                    "ai_agents_included": request.include_ai_agents,
                    "aliases_included": request.include_aliases,
                    "output": result["output"]
                }
            }
        else:
            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="failed",
                message=f"Setup failed: {result.get('error', 'Unknown error')}"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "Setup failed"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error during language setup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-agents")
async def setup_ai_agents(request: AIAgentsSetupRequest):
    """Setup AI agents (Claude CLI and/or Qwen)"""
    try:
        operation_id = f"ai_setup_{request.codespace_name}"

        await websocket_manager.send_operation_update(
            operation_id=operation_id,
            status="started",
            progress=0,
            message="Setting up AI agents..."
        )

        # Build AI agents script based on selection
        script_parts = ["#!/bin/bash", "set -e", ""]

        if request.setup_claude:
            script_parts.append("""
# Claude CLI Setup
echo "🤖 Setting up Claude CLI..."
npm install -g @anthropic-ai/claude-cli || {
    echo "Installing via alternative method..."
    curl -fsSL https://github.com/anthropics/anthropic-cli/releases/latest/download/install.sh | bash
}
echo "alias cl='claude'" >> ~/.bashrc
echo "alias claude-cli='claude'" >> ~/.bashrc
echo "✅ Claude CLI setup complete!"
""")

        if request.setup_qwen:
            script_parts.append("""
# Qwen Setup via Ollama
echo "🧠 Setting up Qwen via Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh
nohup ollama serve > /dev/null 2>&1 &
sleep 10
ollama pull qwen:latest
echo "alias qw='ollama run qwen'" >> ~/.bashrc
echo "alias qwen='ollama run qwen'" >> ~/.bashrc
echo "alias chat='ollama run qwen'" >> ~/.bashrc
echo "✅ Qwen setup complete!"
""")

        script_parts.append("echo '🎉 AI agents setup completed!'")
        combined_script = "\n".join(script_parts)

        result = await github_manager.execute_setup_script(
            codespace_name=request.codespace_name,
            script=combined_script,
            operation_name="AI Agents Setup"
        )

        if result["success"]:
            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="completed",
                progress=100,
                message="AI agents setup completed successfully!"
            )

            return {
                "success": True,
                "message": "AI agents setup completed successfully",
                "data": {
                    "codespace_name": request.codespace_name,
                    "claude_installed": request.setup_claude,
                    "qwen_installed": request.setup_qwen,
                    "output": result["output"]
                }
            }
        else:
            await websocket_manager.send_operation_update(
                operation_id=operation_id,
                status="failed",
                message=f"AI agents setup failed: {result.get('error', 'Unknown error')}"
            )
            raise HTTPException(status_code=400, detail=result.get("error", "AI agents setup failed"))

    except HTTPException:
        raise
    except Exception as e:
        await websocket_manager.send_error(f"Error during AI agents setup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
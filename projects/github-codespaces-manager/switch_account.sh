#!/bin/bash

# Claude Code Account Switcher for Termux
# Usage: ./switch_account.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config file path
CONFIG_FILE="$HOME/.claude_accounts_config"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Config file not found at $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Run setup first: ./setup_accounts.sh${NC}"
    exit 1
fi

# Load configuration
source "$CONFIG_FILE"

# Check if tokens are configured
if [ "$ACCOUNT1_TOKEN" == "your_account1_token_here" ] || [ "$ACCOUNT2_TOKEN" == "your_account2_token_here" ]; then
    echo -e "${RED}Error: Please configure your tokens first${NC}"
    echo -e "${YELLOW}Run: ./setup_accounts.sh${NC}"
    exit 1
fi
CURRENT_DIR=$(pwd)

echo -e "${BLUE}=== Claude Code Account Switcher ===${NC}"
echo -e "${YELLOW}Current directory: $CURRENT_DIR${NC}"

# Step 1: Save current work
echo -e "${BLUE}Step 1: Saving current work...${NC}"
if git rev-parse --git-dir > /dev/null 2>&1; then
    git add .
    git commit -m "WIP: auto-save before account switch $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${GREEN}✓ Work saved to git${NC}"
else
    echo -e "${YELLOW}⚠ Not in a git repository - work not saved${NC}"
fi

# Step 2: Detect current account and switch
echo -e "${BLUE}Step 2: Checking current account...${NC}"

# Determine which account to switch to
if [ "$CURRENT_ACCOUNT" == "1" ]; then
    NEW_TOKEN="$ACCOUNT2_TOKEN"
    NEW_ACCOUNT="2"
    echo -e "${YELLOW}Switching from Account 1 to Account 2${NC}"
else
    NEW_TOKEN="$ACCOUNT1_TOKEN"
    NEW_ACCOUNT="1"
    echo -e "${YELLOW}Switching from Account 2 to Account 1${NC}"
fi

# Step 3: Switch account
echo -e "${BLUE}Step 3: Switching to new account...${NC}"
claude auth --token "$NEW_TOKEN"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully switched accounts${NC}"

    # Update config file with new current account
    sed -i "s/CURRENT_ACCOUNT=.*/CURRENT_ACCOUNT=$NEW_ACCOUNT/" "$CONFIG_FILE"
    echo -e "${GREEN}✓ Updated config file${NC}"
else
    echo -e "${RED}✗ Failed to switch accounts${NC}"
    exit 1
fi

# Step 4: Show instructions
echo -e "${BLUE}Step 4: Ready to continue!${NC}"
echo -e "${GREEN}✓ Account switched successfully${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run: claude code"
echo "2. Navigate to your project if needed: cd $CURRENT_DIR"
echo "3. Check your saved work: git log -1"
echo ""
echo -e "${BLUE}=== Account Switch Complete ===${NC}"

# Optional: Auto-start Claude Code
read -p "Start Claude Code now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Starting Claude Code...${NC}"
    cd "$CURRENT_DIR"
    claude code
fi
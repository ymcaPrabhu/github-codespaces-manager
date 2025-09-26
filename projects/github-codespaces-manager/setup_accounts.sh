#!/bin/bash

# Claude Code Account Setup Script
# Run this once to configure your account tokens

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONFIG_FILE="$HOME/.claude_accounts_config"

echo -e "${BLUE}=== Claude Code Account Setup ===${NC}"
echo -e "${YELLOW}This will help you configure your account tokens${NC}"
echo ""

# Function to get token input
get_token() {
    local account_name=$1
    local token

    echo -e "${BLUE}Setting up $account_name:${NC}"
    echo "1. Go to claude.ai in your browser"
    echo "2. Log into $account_name"
    echo "3. Go to Settings"
    echo "4. Copy the CLI token"
    echo ""

    while true; do
        echo -n "Paste your $account_name token: "
        read -r token

        if [ -z "$token" ]; then
            echo -e "${RED}Token cannot be empty. Please try again.${NC}"
            continue
        fi

        if [ ${#token} -lt 20 ]; then
            echo -e "${RED}Token seems too short. Please check and try again.${NC}"
            continue
        fi

        echo "$token"
        break
    done
}

# Get tokens
echo -e "${YELLOW}Let's set up your two accounts...${NC}"
echo ""

ACCOUNT1_TOKEN=$(get_token "Account 1")
echo ""
ACCOUNT2_TOKEN=$(get_token "Account 2")
echo ""

# Create/update config file
echo -e "${BLUE}Creating configuration file...${NC}"

cat > "$CONFIG_FILE" << EOF
# Claude Code Account Configuration
# Generated on $(date)

# Account 1 Token
ACCOUNT1_TOKEN="$ACCOUNT1_TOKEN"

# Account 2 Token
ACCOUNT2_TOKEN="$ACCOUNT2_TOKEN"

# Current active account (1 or 2)
CURRENT_ACCOUNT=1
EOF

# Set secure permissions
chmod 600 "$CONFIG_FILE"

echo -e "${GREEN}✓ Configuration saved to $CONFIG_FILE${NC}"
echo -e "${GREEN}✓ File permissions set to 600 (secure)${NC}"

# Test first account
echo -e "${BLUE}Testing Account 1...${NC}"
claude auth --token "$ACCOUNT1_TOKEN"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Account 1 is working!${NC}"
else
    echo -e "${RED}✗ Account 1 failed. Please check the token.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo -e "${YELLOW}You can now use: ./switch_account.sh${NC}"
echo -e "${YELLOW}When you hit the 5-hour limit, just run the switch script!${NC}"
echo ""
echo -e "${BLUE}Your tokens are securely stored in: $CONFIG_FILE${NC}"
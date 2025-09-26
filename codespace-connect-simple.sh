#!/bin/bash

# Simple GitHub Codespace Connector
set -e

# Function to connect to codespace
connect_to_codespace() {
    local codespace_name="$1"
    if [[ -z "$codespace_name" ]]; then
        echo "Error: Codespace name is required"
        return 1
    fi

    echo "Connecting to codespace: $codespace_name"
    gh codespace ssh --codespace "$codespace_name"
}

# Main function
main() {
    # Check GitHub CLI authentication
    if ! gh auth status &>/dev/null; then
        echo "Error: GitHub CLI not authenticated"
        echo "Please run: gh auth login"
        exit 1
    fi

    echo "GitHub Codespace Connector"
    echo "========================="
    echo

    # Get codespace name from user
    read -p "Enter codespace name: " codespace_name

    if [[ -z "$codespace_name" ]]; then
        echo "Error: Codespace name cannot be empty"
        exit 1
    fi

    connect_to_codespace "$codespace_name"
}

# Handle command line argument or run interactive mode
if [[ $# -eq 1 ]]; then
    connect_to_codespace "$1"
else
    main
fi
#!/usr/bin/env bash

# Quick Start Script - Zero to GitHub Codespaces in minutes
echo "🚀 GitHub Codespaces Manager - Quick Start"
echo "=========================================="

# Check if in Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "⚠️  This script is optimized for Termux"
    echo "    Some features may not work on other systems"
fi

echo "This will:"
echo "  1. Install missing dependencies"
echo "  2. Set up the application"
echo "  3. Launch the Quick Start wizard"
echo

read -p "Continue? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 0
fi

# Run installation
echo "📦 Running installation..."
if [ -f "install.sh" ]; then
    ./install.sh
else
    # Fallback
    python3 setup.py
fi

echo
echo "🎯 Launching Quick Start wizard..."
echo "   Select option 11 from the main menu"
echo

# Launch application
./codespaces-manager.py

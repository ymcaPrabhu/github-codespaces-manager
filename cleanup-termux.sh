#!/bin/bash

# Termux Storage Cleanup Script
# Automatically cleans caches, temporary files, and logs

echo "🧹 Starting Termux cleanup..."

# Check initial disk usage
echo "📊 Initial disk usage:"
du -sh ~

echo ""
echo "🗑️  Cleaning package manager cache..."
pkg clean >/dev/null 2>&1

echo "🗑️  Removing orphaned packages..."
apt autoremove -y >/dev/null 2>&1

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

echo "🗑️  Cleaning download cache..."
find ~/Downloads -name "*.deb" -type f -mtime +7 -delete 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo "📊 Final disk usage:"
du -sh ~

echo ""
echo "💾 Cleanup finished on $(date)"
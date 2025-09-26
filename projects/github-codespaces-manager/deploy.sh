#!/usr/bin/env bash

# GitHub Codespaces Manager - Final Deployment Script
# Creates a complete, ready-to-distribute package

set -e

echo "🚀 GitHub Codespaces Manager - Deployment Script"
echo "================================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PROJECT_NAME="github-codespaces-manager"
VERSION="1.0.0"
BUILD_DIR="dist"
PACKAGE_DIR="$BUILD_DIR/$PROJECT_NAME-$VERSION"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Clean and create build directory
print_step "Setting up build environment..."
rm -rf "$BUILD_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy core files
print_step "Copying application files..."
cp codespaces-manager.py "$PACKAGE_DIR/" || {
    print_error "Main script not found!"
    exit 1
}

cp codespaces_advanced.py "$PACKAGE_DIR/" || {
    print_error "Advanced module not found!"
    exit 1
}

# Copy documentation
print_step "Copying documentation..."
cp README.md "$PACKAGE_DIR/"
cp install.sh "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/codespaces-manager.py"
chmod +x "$PACKAGE_DIR/install.sh"

# Create additional deployment files
print_step "Creating deployment metadata..."

# Create VERSION file
echo "$VERSION" > "$PACKAGE_DIR/VERSION"

# Create .gitignore
cat > "$PACKAGE_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env

# Configuration and logs
.config/
.local/
.cache/
*.log

# OS
.DS_Store
Thumbs.db
*~

# IDE
.vscode/
.idea/
*.swp
*.swo

# Package builds
dist/
build/
*.egg-info/
EOF

# Create LICENSE file
cat > "$PACKAGE_DIR/LICENSE" << 'EOF'
MIT License

Copyright (c) 2025 GitHub Codespaces Manager

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create requirements.txt
cat > "$PACKAGE_DIR/requirements.txt" << 'EOF'
psutil>=5.8.0
EOF

# Create setup script for easy deployment
cat > "$PACKAGE_DIR/setup.py" << 'EOF'
#!/usr/bin/env python3
"""
Setup script for GitHub Codespaces Manager
"""

from pathlib import Path
import shutil
import subprocess
import sys

def main():
    print("🔧 GitHub Codespaces Manager Setup")
    print("==================================")

    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return 1

        print("✅ Python version OK")

        # Install dependencies
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                      check=True)
        print("✅ Dependencies installed")

        # Create symlink if possible
        home = Path.home()
        bin_dir = home / "../usr/bin"

        if bin_dir.exists():
            symlink_path = bin_dir / "codespaces-manager"
            main_script = Path.cwd() / "codespaces-manager.py"

            if symlink_path.exists():
                symlink_path.unlink()

            try:
                symlink_path.symlink_to(main_script)
                print(f"✅ Created command: codespaces-manager")
            except OSError:
                print("⚠️  Could not create command symlink")

        print("\n🎉 Setup complete!")
        print("\nTo run:")
        print("  ./codespaces-manager.py")
        print("  # or (if symlink was created)")
        print("  codespaces-manager")

        return 0

    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return 1
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x "$PACKAGE_DIR/setup.py"

# Create enhanced quick start script
cat > "$PACKAGE_DIR/quickstart.sh" << 'EOF'
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
EOF

chmod +x "$PACKAGE_DIR/quickstart.sh"

# Generate file list and checksums
print_step "Generating manifest and checksums..."

cd "$PACKAGE_DIR"
find . -type f -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" | sort > MANIFEST

# Create checksums for verification
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum * > SHA256SUMS
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 * > SHA256SUMS
fi

cd - >/dev/null

# Create compressed archive
print_step "Creating distribution archives..."

cd "$BUILD_DIR"

# Create tar.gz
tar -czf "${PROJECT_NAME}-${VERSION}.tar.gz" "${PROJECT_NAME}-${VERSION}/"
print_status "Created: ${PROJECT_NAME}-${VERSION}.tar.gz"

# Create zip
if command -v zip >/dev/null 2>&1; then
    zip -r "${PROJECT_NAME}-${VERSION}.zip" "${PROJECT_NAME}-${VERSION}/" >/dev/null
    print_status "Created: ${PROJECT_NAME}-${VERSION}.zip"
fi

cd - >/dev/null

# Generate deployment summary
print_step "Generating deployment summary..."

cat > "$BUILD_DIR/DEPLOYMENT_SUMMARY.txt" << EOF
GitHub Codespaces Manager v$VERSION
===================================

📦 Package Contents:
- codespaces-manager.py     Main application
- codespaces_advanced.py    Advanced features module
- README.md                 Comprehensive documentation
- install.sh                Automated installer for Termux
- quickstart.sh             Zero-config quick start
- setup.py                  Python-based setup script
- requirements.txt          Python dependencies
- LICENSE                   MIT License
- .gitignore               Git ignore patterns

🚀 Deployment Options:

1. QUICK START (Recommended):
   tar -xzf ${PROJECT_NAME}-${VERSION}.tar.gz
   cd ${PROJECT_NAME}-${VERSION}
   ./quickstart.sh

2. MANUAL INSTALLATION:
   tar -xzf ${PROJECT_NAME}-${VERSION}.tar.gz
   cd ${PROJECT_NAME}-${VERSION}
   ./install.sh

3. PYTHON SETUP:
   tar -xzf ${PROJECT_NAME}-${VERSION}.tar.gz
   cd ${PROJECT_NAME}-${VERSION}
   python3 setup.py

📋 System Requirements:
- Android device with Termux (recommended)
- Python 3.8+
- Git and GitHub CLI
- Internet connection
- ~50MB free storage

✨ Key Features:
- Complete GitHub repository management
- Codespaces lifecycle automation
- System monitoring and cleanup
- Development environment bootstrap
- SSH key management
- Cost tracking and optimization

🔗 First Run:
After installation, run ./codespaces-manager.py and select
"Quick Start Wizard" (option 11) for guided setup.

📖 Documentation:
Full documentation available in README.md

Generated on: $(date)
EOF

print_status "Deployment summary created"

# Show final results
print_step "Deployment complete!"

echo
echo -e "${GREEN}📦 Package Information:${NC}"
echo -e "   Name: ${CYAN}$PROJECT_NAME${NC}"
echo -e "   Version: ${CYAN}$VERSION${NC}"
echo -e "   Location: ${CYAN}$BUILD_DIR${NC}"
echo

echo -e "${GREEN}📁 Created Files:${NC}"
ls -la "$BUILD_DIR" | grep -E "\.(tar\.gz|zip)$" | while read -r line; do
    echo -e "   ${CYAN}$(echo $line | awk '{print $9}')${NC} ($(echo $line | awk '{print $5}') bytes)"
done

echo
echo -e "${GREEN}🚀 Quick Deployment Command:${NC}"
echo -e "   ${CYAN}tar -xzf $BUILD_DIR/${PROJECT_NAME}-${VERSION}.tar.gz${NC}"
echo -e "   ${CYAN}cd ${PROJECT_NAME}-${VERSION}${NC}"
echo -e "   ${CYAN}./quickstart.sh${NC}"

echo
echo -e "${GREEN}✅ Ready for distribution!${NC}"

# Offer to test the package
echo
read -p "Test the packaged version? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_step "Testing packaged version..."

    cd "$BUILD_DIR"
    tar -xzf "${PROJECT_NAME}-${VERSION}.tar.gz"
    cd "${PROJECT_NAME}-${VERSION}"

    if ./codespaces-manager.py --version >/dev/null 2>&1; then
        print_status "✅ Package test successful!"
    else
        print_warning "⚠️  Package test had issues"
    fi

    cd - >/dev/null
fi

print_status "🎉 GitHub Codespaces Manager deployment completed successfully!"
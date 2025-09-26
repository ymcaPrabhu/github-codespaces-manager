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

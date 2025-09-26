#!/usr/bin/env python3
"""
Quick test script for development environment features
"""
import subprocess
import sys
import os

def test_codespace_availability():
    """Check if codespaces are available"""
    try:
        result = subprocess.run(['gh', 'codespace', 'list'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if result.stdout.strip():
                print("✅ Codespaces available:")
                print(result.stdout)
                return True
            else:
                print("❌ No codespaces found. Create one first:")
                print("   gh codespace create")
                return False
        else:
            print(f"❌ GitHub CLI error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking codespaces: {e}")
        return False

def test_development_features():
    """Test the development environment features"""
    print("🧪 Testing GitHub Codespaces Manager Development Features\n")

    # Check GitHub CLI
    try:
        result = subprocess.run(['gh', 'auth', 'status'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ GitHub CLI authenticated")
        else:
            print("❌ GitHub CLI not authenticated")
            return False
    except:
        print("❌ GitHub CLI not found")
        return False

    # Check codespaces
    if not test_codespace_availability():
        return False

    # Test main application can start
    try:
        # Test that the main file can be imported/parsed
        with open('codespaces-manager.py', 'r') as f:
            content = f.read()
            if 'language_environment_menu' in content:
                print("✅ Development environment functions found in code")
            else:
                print("❌ Development environment functions missing")
                return False
    except:
        print("❌ Cannot read main application file")
        return False

    print("\n🎯 All prerequisites met! Development features should work.")
    print("\nTo use:")
    print("1. python3 codespaces-manager.py")
    print("2. Choose option 7 (Codespaces Lifecycle)")
    print("3. Choose option 8 (Language & Development Environment Setup)")

    return True

if __name__ == "__main__":
    os.chdir('/data/data/com.termux/files/home/projects/github-codespaces-manager')
    success = test_development_features()
    sys.exit(0 if success else 1)
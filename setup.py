"""
Setup script for Windows Desktop Automator.
Validates environment and installs dependencies.
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def check_windows_version():
    """Check if running on Windows."""
    if platform.system() != 'Windows':
        print(f"❌ Windows required. Current OS: {platform.system()}")
        return False
    print(f"✅ Windows {platform.release()} detected")
    return True

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    try:
        print("📦 Installing Python dependencies...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        'artifacts/logs',
        'artifacts/screens',
        'artifacts/ocr_debug'
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def run_basic_tests():
    """Run basic functionality tests."""
    print("🧪 Running basic tests...")
    
    # Test recipe validation
    try:
        result = subprocess.run([
            sys.executable, 'validate_recipe.py', 'recipes/notepad_excel.yaml'
        ], check=True, capture_output=True, text=True)
        print("✅ Recipe validation test passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Recipe validation test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Windows Desktop Automator Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_windows_version() or not check_python_version():
        print("\n❌ Setup failed - prerequisites not met")
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("\n❌ Setup failed - could not install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run basic tests
    print("\n🧪 Running validation tests...")
    if not run_basic_tests():
        print("\n⚠️  Setup completed but tests failed")
        print("You can still use the automator, but some features may not work correctly")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Validate the sample recipe:")
    print("   python validate_recipe.py recipes\\notepad_excel.yaml")
    print("\n2. Run the sample automation (requires dependencies):")
    print("   python automator_cli.py run recipes\\notepad_excel.yaml --dry-run")
    print("\n3. Check available providers:")
    print("   python automator_cli.py list-providers")

if __name__ == "__main__":
    main()
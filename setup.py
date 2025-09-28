"""
Setup script for Windows Desktop Automator.
Validates environment and installs dependencies.
"""

import os
import sys
import subprocess
import platform

# Safe print function for Unicode/emoji handling
def safe_print(text: str) -> None:
    """Print text with emoji fallbacks for Windows compatibility."""
    emoji_fallbacks = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '🚀': '>>',
        '📍': '*',
        '🎉': '[SUCCESS]',
        '💥': '[FAILED]',
        '⚠️': '[WARNING]',
        '🧪': '[TEST]',
        '📦': '[PACKAGE]',
        '📁': '[FOLDER]'
    }
    
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace emojis with ASCII fallbacks
        safe_text = text
        for emoji, fallback in emoji_fallbacks.items():
            safe_text = safe_text.replace(emoji, fallback)
        print(safe_text)

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        safe_print(f"❌ Python 3.11+ required. Current version: {version.major}.{version.minor}")
        return False
    safe_print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def check_windows_version():
    """Check if running on Windows."""
    if platform.system() != 'Windows':
        safe_print(f"❌ Windows required. Current OS: {platform.system()}")
        return False
    safe_print(f"✅ Windows {platform.release()} detected")
    return True

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    try:
        safe_print("📦 Installing Python dependencies...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True, text=True)
        safe_print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"❌ Failed to install dependencies: {e}")
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
        safe_print(f"✅ Created directory: {dir_path}")

def run_basic_tests():
    """Run basic functionality tests."""
    safe_print("🧪 Running basic tests...")
    
    # Test recipe validation
    try:
        result = subprocess.run([
            sys.executable, 'validate_recipe.py', 'recipes/notepad_excel.yaml'
        ], check=True, capture_output=True, text=True)
        safe_print("✅ Recipe validation test passed")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"❌ Recipe validation test failed: {e}")
        return False

def main():
    """Main setup function."""
    safe_print("🚀 Windows Desktop Automator Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_windows_version() or not check_python_version():
        safe_print("\n❌ Setup failed - prerequisites not met")
        sys.exit(1)
    
    # Create directories
    safe_print("\n📁 Creating directories...")
    create_directories()
    
    # Install dependencies
    safe_print("\n📦 Installing dependencies...")
    if not install_dependencies():
        safe_print("\n❌ Setup failed - could not install dependencies")
        print("Try running manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run basic tests
    safe_print("\n🧪 Running validation tests...")
    if not run_basic_tests():
        safe_print("\n⚠️  Setup completed but tests failed")
        print("You can still use the automator, but some features may not work correctly")
    
    safe_print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Validate the sample recipe:")
    print("   python validate_recipe.py recipes\\notepad_excel.yaml")
    print("\n2. Run the sample automation (requires dependencies):")
    print("   python automator_cli.py run recipes\\notepad_excel.yaml --dry-run")
    print("\n3. Check available providers:")
    print("   python automator_cli.py list-providers")

if __name__ == "__main__":
    main()
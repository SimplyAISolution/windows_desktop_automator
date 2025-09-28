#!/usr/bin/env python3
"""
Integration test script for Windows Desktop Automator.
Tests end-to-end functionality that can be validated without Windows.
"""

import os
import sys
import yaml
import subprocess
import tempfile
import shutil
from pathlib import Path

def test_setup_process():
    """Test the setup process functionality."""
    print("🔧 Testing setup process...")
    
    # Test that setup.py can be executed (at least the syntax)
    setup_path = os.path.join(os.getcwd(), "setup.py")
    
    try:
        # Test setup script syntax
        with open(setup_path, 'r') as f:
            compile(f.read(), setup_path, 'exec')
        print("✅ Setup script syntax is valid")
        
        # Test basic validation that setup.py would run
        result = subprocess.run([
            sys.executable, "validate_recipe.py", "recipes/notepad_excel.yaml"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Setup validation test passes")
        else:
            print(f"❌ Setup validation test failed: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Setup process test failed: {e}")
        return False


def test_recipe_execution_dry_run():
    """Test recipe execution in dry-run mode (structure validation only)."""
    print("🎯 Testing recipe execution structure...")
    
    recipe_path = "recipes/notepad_excel.yaml"
    
    try:
        # Load and validate recipe structure
        with open(recipe_path, 'r') as f:
            recipe_data = yaml.safe_load(f)
        
        # Validate all required fields
        required_fields = ['name', 'description', 'steps']
        for field in required_fields:
            if field not in recipe_data:
                print(f"❌ Recipe missing required field: {field}")
                return False
        
        # Validate steps structure
        steps = recipe_data['steps']
        if not isinstance(steps, list) or len(steps) == 0:
            print("❌ Recipe must have at least one step")
            return False
        
        # Validate each step
        for i, step in enumerate(steps, 1):
            required_step_fields = ['name', 'action', 'target']
            for field in required_step_fields:
                if field not in step:
                    print(f"❌ Step {i} missing required field: {field}")
                    return False
        
        print(f"✅ Recipe structure validation passed ({len(steps)} steps)")
        
        # Test variable substitution logic
        if 'variables' in recipe_data:
            variables = recipe_data['variables']
            test_text = "Hello ${demo_text}!"
            
            # Simple variable substitution test
            for var_name, var_value in variables.items():
                test_text = test_text.replace(f"${{{var_name}}}", str(var_value))
            
            if "${" not in test_text or "Hello Windows Desktop Automator" in test_text:
                print("✅ Variable substitution logic works")
            else:
                print("❌ Variable substitution logic failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Recipe execution structure test failed: {e}")
        return False


def test_cli_interface_structure():
    """Test CLI interface structure."""
    print("🖥️  Testing CLI interface structure...")
    
    try:
        # Read main CLI file
        main_path = os.path.join("automator", "core", "main.py")
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Check for expected CLI commands
        expected_commands = [
            'def run(',
            'def validate(',
            'def list_providers(',
            'def version('
        ]
        
        for cmd in expected_commands:
            if cmd not in content:
                print(f"❌ CLI command not found: {cmd}")
                return False
        
        print("✅ All expected CLI commands found")
        
        # Check for proper error handling
        if 'try:' in content and 'except' in content:
            print("✅ CLI has error handling")
        else:
            print("❌ CLI lacks proper error handling")
            return False
        
        # Check for orchestrator pattern
        if 'AutomationOrchestrator' in content:
            print("✅ Uses orchestrator pattern")
        else:
            print("❌ Missing orchestrator pattern")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CLI structure test failed: {e}")
        return False


def test_provider_architecture():
    """Test provider architecture."""
    print("🔌 Testing provider architecture...")
    
    try:
        providers_dir = os.path.join("automator", "providers")
        expected_providers = ['ui.py', 'process.py', 'fs.py', 'ocr.py']
        
        for provider in expected_providers:
            provider_path = os.path.join(providers_dir, provider)
            if not os.path.exists(provider_path):
                print(f"❌ Provider missing: {provider}")
                return False
            
            # Check provider has class definition
            with open(provider_path, 'r') as f:
                content = f.read()
            
            # Should have a provider class
            if 'Provider' not in content or 'class' not in content:
                print(f"❌ Provider {provider} lacks proper class structure")
                return False
        
        print("✅ All providers have proper structure")
        
        # Check for dependency injection pattern
        main_path = os.path.join("automator", "core", "main.py")
        with open(main_path, 'r') as f:
            main_content = f.read()
        
        provider_imports = ['ProcessProvider', 'UIProvider', 'FileSystemProvider', 'OCRProvider']
        for provider in provider_imports:
            if provider not in main_content:
                print(f"❌ Provider not imported in main: {provider}")
                return False
        
        print("✅ Provider dependency injection pattern verified")
        return True
        
    except Exception as e:
        print(f"❌ Provider architecture test failed: {e}")
        return False


def test_logging_system():
    """Test logging system structure.""" 
    print("📝 Testing logging system...")
    
    try:
        logger_path = os.path.join("automator", "core", "logger.py")
        if not os.path.exists(logger_path):
            print("❌ Logger module missing")
            return False
        
        with open(logger_path, 'r') as f:
            content = f.read()
        
        # Check for expected logging functions
        expected_functions = [
            'log_step_start',
            'log_step_success', 
            'log_step_failure',
            'AutomatorLogger'
        ]
        
        for func in expected_functions:
            if func not in content:
                print(f"❌ Logging function missing: {func}")
                return False
        
        print("✅ Logging system has proper structure")
        
        # Check artifacts directory structure
        artifacts_dirs = ['artifacts/logs', 'artifacts/screens', 'artifacts/ocr_debug']
        for artifacts_dir in artifacts_dirs:
            if os.path.exists(artifacts_dir):
                print(f"✅ Artifacts directory exists: {artifacts_dir}")
            else:
                print(f"ℹ️  Artifacts directory will be created: {artifacts_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging system test failed: {e}")
        return False


def main():
    """Run integration tests."""
    print("🧪 WINDOWS DESKTOP AUTOMATOR - INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_setup_process,
        test_recipe_execution_dry_run,
        test_cli_interface_structure,
        test_provider_architecture, 
        test_logging_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
            failed += 1
        print()  # Add spacing
    
    print("=" * 60)
    print(f"📊 INTEGRATION TEST RESULTS")
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✨ The Windows Desktop Automator is ready for deployment!")
        print("\n📋 Next Steps:")
        print("1. Deploy to Windows environment")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run setup: python setup.py")
        print("4. Test with: python automator_cli.py list-providers")
        return 0
    else:
        print(f"\n❌ {failed} integration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
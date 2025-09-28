# Test Suite Documentation

This document describes the comprehensive test suite for the Windows Desktop Automator project.

## Overview

The test suite ensures that all components of the Windows Desktop Automator work properly together, even when run in environments without Windows-specific dependencies.

## Test Scripts

### 1. `run_all_tests.py` - Main Test Runner
The primary entry point for all testing.

```bash
# Run all tests with detailed report
python run_all_tests.py --report

# Run quick tests only
python run_all_tests.py --quick
```

**Test Suites:**
- Project Structure Validation
- Basic Recipe Validation  
- Setup Script Validation
- Integration Tests
- Unit Tests (when dependencies available)

### 2. `test_integration.py` - Integration Tests
Tests end-to-end functionality and architecture.

```bash
python test_integration.py
```

**Tests:**
- Setup process functionality
- Recipe execution structure
- CLI interface structure  
- Provider architecture
- Logging system

### 3. `validate_recipe.py` - Recipe Validation
Basic recipe structure validation without dependencies.

```bash
python validate_recipe.py recipes/notepad_excel.yaml
```

## Test Coverage

### ✅ Fully Tested (Linux Compatible)
- **Core Architecture**: File structure, imports, syntax validation
- **Recipe Processing**: YAML parsing, structure validation, variable substitution  
- **CLI Structure**: Command definitions, argument parsing, help system
- **Setup Process**: Installation logic, directory creation, validation
- **Error Handling**: Exception handling patterns, error recovery
- **Documentation**: README completeness, inline documentation

### ⚠️ Requires Windows Environment
- **UI Automation**: pywinauto integration, UIA backend functionality
- **OCR Processing**: pytesseract integration, image processing
- **Live Automation**: Actual application interaction, screenshot capture
- **Hardware Integration**: Windows-specific APIs, system integration

### 📋 Future Testing
- **Performance Testing**: Load testing, timing analysis, memory usage
- **Stress Testing**: Long-running automation scenarios
- **Edge Cases**: Error recovery, timeout handling, resource cleanup

## Running Tests in Different Environments

### Linux/CI Environment (Current)
```bash
# Full test suite
python run_all_tests.py --report

# Quick validation
python validate_recipe.py recipes/notepad_excel.yaml
```

### Windows Development Environment
```bash
# Install dependencies first
pip install -r requirements.txt

# Run setup
python setup.py

# Full test suite
python run_all_tests.py --report

# Test providers
python automator_cli.py list-providers

# Test recipe execution (dry run)
python automator_cli.py run recipes/notepad_excel.yaml --dry-run
```

### Windows Production Environment
```bash
# Full integration test
python automator_cli.py run recipes/notepad_excel.yaml

# Provider availability
python automator_cli.py list-providers
```

## Test Results Interpretation

### 100% Pass Rate
- Framework is structurally sound
- Ready for Windows deployment
- All validation logic works correctly

### Partial Failures
- Check specific test outputs for issues
- Common causes: missing files, syntax errors, structural problems
- Fix issues before deployment

### Dependency-Related Failures
- Expected in non-Windows environments
- Indicates need for proper environment setup
- Does not affect core framework integrity

## Continuous Integration

The test suite is designed to work in GitHub Actions and other CI environments:

```yaml
# Example CI configuration
- name: Test Windows Desktop Automator
  run: |
    cd windows_desktop_automator
    python run_all_tests.py --report
```

## Adding New Tests

### For Core Functionality
Add tests to the appropriate section in `run_all_tests.py` or `test_integration.py`.

### For Provider-Specific Functionality  
Add tests to `tests/test_dsl.py` using pytest framework.

### For Recipe Validation
Extend `validate_recipe.py` with additional validation rules.

## Test Maintenance

- Update tests when adding new features
- Maintain compatibility with Linux testing environment
- Ensure Windows-specific tests are clearly marked
- Keep test documentation current

## Troubleshooting

### Common Issues
1. **Import Errors**: Usually dependency-related, expected in Linux
2. **Timeout Errors**: Increase timeout values in test scripts  
3. **File Not Found**: Check working directory and file paths
4. **Permission Errors**: Ensure test scripts have execute permissions

### Debug Mode
Run tests with Python's verbose output:
```bash
python -v run_all_tests.py --report
```
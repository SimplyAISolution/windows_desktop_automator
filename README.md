# Windows Desktop Automator

A powerful Python-based automation framework for Windows desktop applications using UI automation, OCR, and file operations. Executes YAML-based recipes with comprehensive retry logic, logging, and error handling.

## 🚀 Features

- **UI Automation**: Native Windows UI automation using pywinauto with UIA backend
- **OCR Support**: Optical character recognition with pytesseract for text extraction
- **File Operations**: Secure file system operations with path validation
- **Process Management**: Application lifecycle management with idempotency
- **YAML Recipes**: Human-readable automation scripts with variable substitution
- **Robust Error Handling**: Comprehensive retry logic with exponential backoff
- **Rich Logging**: Structured JSON logging with screenshot capture on failure
- **CLI Interface**: Easy-to-use command line interface with progress tracking

## 📋 Requirements

- Windows 11 (recommended) or Windows 10
- Python 3.11+
- PowerShell 7+
- Required Python packages (see requirements.txt)

## 🛠️ Installation

1. **Clone the repository**:
   ```powershell
   git clone <https://github.com/SimplyAISolution/windows_desktop_automator.git>
   cd windows_desktop_automator
   ```

2. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Optional: Install Tesseract OCR** (for enhanced text recognition):
   - Download from: https://github.com/tesseract-ocr/tesseract
   - Add to system PATH or specify path in configuration

## 🎯 Quick Start

### 1. Validate the Sample Recipe
```powershell
python validate_recipe.py recipes\notepad_excel.yaml
```

### 2. Run the Demo Recipe
```powershell
# With dependencies installed:
python automator_cli.py run recipes\notepad_excel.yaml

# Dry run (validation only):
python automator_cli.py run recipes\notepad_excel.yaml --dry-run
```

### 3. Check Available Providers
```powershell
python automator_cli.py list-providers
```

## 📖 Recipe Structure

Recipes are YAML files that describe automation workflows:

```yaml
name: "my_automation"
description: "Example automation recipe"
version: "1.0"
variables:
  app_name: "notepad.exe"
  demo_text: "Hello World!"

steps:
  - name: "Launch Application"
    action: "launch"
    target:
      app: "${app_name}"
    timeout: 15
    retry_attempts: 3
    
  - name: "Wait for Window"
    action: "wait_for"
    target:
      window:
        name: "Untitled - Notepad"
    timeout: 10
    
  - name: "Type Text"
    action: "type"
    target:
      element:
        control_type: "Edit"
        class_name: "Edit"
      text: "${demo_text}"
    verify_after: true
```

## 🎮 Action Types

### Application Control
- `launch`: Start applications
- `wait_for`: Wait for windows/elements to appear
- `verify`: Verify element states

### UI Interaction
- `click`: Click UI elements (left, right, double)
- `type`: Type text into elements
- `hotkey`: Send keyboard shortcuts
- `read_text`: Extract text from elements

### File Operations
- `file_read`: Read text files
- `file_write`: Write text files
- `file_copy`: Copy files

### Advanced
- `screenshot`: Capture screen/window screenshots
- `ocr_text`: Extract text using OCR

## 🔧 Element Selectors

Target UI elements using multiple strategies:

### High Precision (Recommended)
```yaml
element:
  automation_id: "btn_submit"  # Most reliable
  control_type: "Button"       # Additional specificity
```

### Medium Precision
```yaml
element:
  control_type: "Edit"
  name: "Username"
  class_name: "TextBox"
```

### Fallback Options
```yaml
element:
  name: "Submit"      # Text-based matching
  index: 0            # Position-based selection
```

## 🏗️ Architecture

### Core Components
- **`automator/core/main.py`**: CLI orchestrator with retry logic
- **`automator/core/dsl.py`**: Recipe schema and validation
- **`automator/core/logger.py`**: Structured logging with screenshots

### Providers
- **`automator/providers/ui.py`**: UI automation (pywinauto + UIA)
- **`automator/providers/process.py`**: Application lifecycle
- **`automator/providers/fs.py`**: File system operations
- **`automator/providers/ocr.py`**: Optical character recognition

## 📊 Logging & Monitoring

### Structured Logging
- JSON format logs in `artifacts/logs/`
- Screenshots on failure in `artifacts/screens/`
- Step-by-step execution tracking

### Log Entry Example
```json
{
  "step_id": "20241227_143022_001",
  "action": "click_element",
  "target": "Submit Button",
  "phase": "SUCCESS",
  "timestamp": "2024-12-27T14:30:22.123456",
  "result": "Element clicked successfully"
}
```

## 🧪 Testing

### Run Unit Tests
```powershell
pytest tests/
```

### Validate Recipe Structure
```powershell
python validate_recipe.py recipes/your_recipe.yaml
```

### Integration Testing
```powershell
# Test with dry run
python automator_cli.py run recipes/notepad_excel.yaml --dry-run
```

## 🔒 Security Features

- **Path Validation**: Restricts file operations to allowed directories
- **Process Isolation**: Safe application lifecycle management
- **Secret Handling**: No credentials in logs (use .env files)
- **Error Sanitization**: Removes sensitive data from error messages

## 📝 Recipe Variables

Use variables for dynamic content:

```yaml
variables:
  username: "testuser"
  data_file: "artifacts/test_data.txt"
  timestamp: "${current_datetime}"

steps:
  - name: "Login"
    action: "type"
    target:
      text: "${username}"
```

## 🛡️ Best Practices

### Element Selection
1. **Use AutomationId when available** (highest reliability)
2. **Combine multiple selectors** for specificity
3. **Test selectors thoroughly** across different UI states

### Recipe Design
1. **Include verification steps** after critical actions
2. **Use appropriate timeouts** (5-15 seconds typical)
3. **Enable continue_on_failure** for non-critical steps
4. **Add meaningful step names** for debugging

### Error Handling
1. **Set realistic retry counts** (3-5 attempts)
2. **Use progressive delays** between retries
3. **Include cleanup steps** in recipes
4. **Monitor log outputs** for patterns

## 🚨 Troubleshooting

### Common Issues

**Element Not Found**
```
Solution: Verify element selectors using Windows Spy tools
- Use Inspect.exe (Windows SDK)
- Check AutomationId, ControlType, ClassName
- Consider timing issues (add wait_for steps)
```

**Application Launch Timeout**
```
Solution: Increase timeout or verify application path
- Check application is installed and accessible
- Verify no permission issues
- Consider antivirus interference
```

**OCR Not Working**
```
Solution: Install and configure Tesseract OCR
- Download from: https://github.com/tesseract-ocr/tesseract
- Add to system PATH
- Verify with: tesseract --version
```

### Debug Mode
Enable verbose logging:
```powershell
python automator_cli.py run recipes/your_recipe.yaml --verbose
```

## 📚 Advanced Usage

### Custom Providers
Extend the framework by creating custom providers:

```python
from automator.core.logger import automator_logger

class CustomProvider:
    def custom_action(self, target, **kwargs):
        step_id = automator_logger.log_step_start("custom_action", target)
        try:
            # Your implementation here
            result = self.do_something()
            automator_logger.log_step_success(step_id, "custom_action", target, result)
            return True
        except Exception as e:
            automator_logger.log_step_failure(step_id, "custom_action", target, e)
            return False
```

### Integration with CI/CD
Use the automator in automated testing pipelines:

```powershell
# PowerShell script for CI
$result = python automator_cli.py run recipes/smoke_test.yaml
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Automation tests passed"
} else {
    Write-Host "❌ Automation tests failed"
    exit 1
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in `artifacts/logs/`
3. Create an issue with recipe and log files
4. Include system information (Windows version, Python version)

---

**Built with ❤️ for Windows automation**

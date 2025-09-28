"""
Main orchestrator for the Windows Desktop Automator.
CLI interface that loads YAML recipes, executes automation steps with retry logic,
and provides comprehensive logging and error handling.
"""

import os
import sys
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.progress import Progress, TaskID
from rich.table import Table

from automator.core.console_utils import console
from automator.core.dsl import Recipe, ActionStep, ActionType, RecipeValidationError, load_recipe_from_dict
from automator.core.logger import automator_logger
from automator.providers.process import ProcessProvider  
from automator.providers.ui import UIProvider
from automator.providers.fs import FileSystemProvider
from automator.providers.ocr import OCRProvider


app = typer.Typer(help="Windows Desktop Automator - Execute automation recipes")


class AutomationOrchestrator:
    """Main orchestrator for executing automation recipes."""
    
    def __init__(self):
        """Initialize orchestrator with providers."""
        self.process_provider = ProcessProvider()
        self.ui_provider = UIProvider()
        self.fs_provider = FileSystemProvider()
        self.ocr_provider = OCRProvider()
        
        self._recipe: Optional[Recipe] = None
        self._current_step = 0
        self._start_time = 0.0
    
    def load_recipe(self, recipe_path: str) -> bool:
        """
        Load and validate recipe from YAML file.
        
        Args:
            recipe_path: Path to recipe YAML file
            
        Returns:
            True if recipe loaded successfully
        """
        try:
            with open(recipe_path, 'r', encoding='utf-8') as f:
                recipe_data = yaml.safe_load(f)
            
            self._recipe = load_recipe_from_dict(recipe_data)
            
            console.print(f"✅ Loaded recipe: {self._recipe.name}")
            console.print(f"   Description: {self._recipe.description}")
            console.print(f"   Steps: {len(self._recipe.steps)}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ Failed to load recipe: {e}")
            return False
    
    def execute_recipe(self) -> bool:
        """
        Execute the loaded recipe with comprehensive error handling.
        
        Returns:
            True if all steps completed successfully
        """
        if not self._recipe:
            console.print("❌ No recipe loaded")
            return False
        
        self._start_time = time.time()
        self._current_step = 0
        
        automator_logger.log_recipe_start(self._recipe.name, "loaded_from_memory")
        
        console.print(f"\n🚀 Executing recipe: {self._recipe.name}")
        
        success = True
        
        with Progress() as progress:
            task = progress.add_task("Executing steps...", total=len(self._recipe.steps))
            
            for i, step in enumerate(self._recipe.steps):
                self._current_step = i + 1
                
                console.print(f"\n📍 Step {self._current_step}/{len(self._recipe.steps)}: {step.name}")
                
                step_success = self._execute_step(step)
                
                if step_success:
                    console.print(f"✅ Step completed: {step.name}")
                else:
                    console.print(f"❌ Step failed: {step.name}")
                    if not step.continue_on_failure:
                        success = False
                        break
                
                progress.update(task, advance=1)
        
        duration = time.time() - self._start_time
        
        if success:
            automator_logger.log_recipe_complete(self._recipe.name, len(self._recipe.steps), duration)
            console.print(f"\n🎉 Recipe completed successfully in {duration:.2f}s")
        else:
            automator_logger.log_recipe_failure(self._recipe.name, self._current_step, 
                                              Exception("Recipe execution failed"))
            console.print(f"\n💥 Recipe failed at step {self._current_step} after {duration:.2f}s")
        
        return success
    
    def _execute_step(self, step: ActionStep) -> bool:
        """Execute individual automation step with retries."""
        last_error = None
        
        for attempt in range(1, step.retry_attempts + 1):
            try:
                # Substitute variables in step
                substituted_step = self._substitute_step_variables(step)
                
                # Execute based on action type
                if substituted_step.action == ActionType.LAUNCH:
                    result = self._execute_launch_action(substituted_step)
                elif substituted_step.action == ActionType.WAIT_FOR:
                    result = self._execute_wait_for_action(substituted_step)
                elif substituted_step.action == ActionType.CLICK:
                    result = self._execute_click_action(substituted_step)
                elif substituted_step.action == ActionType.TYPE:
                    result = self._execute_type_action(substituted_step)
                elif substituted_step.action == ActionType.HOTKEY:
                    result = self._execute_hotkey_action(substituted_step)
                elif substituted_step.action == ActionType.VERIFY:
                    result = self._execute_verify_action(substituted_step)
                elif substituted_step.action == ActionType.READ_TEXT:
                    result = self._execute_read_text_action(substituted_step)
                elif substituted_step.action == ActionType.FILE_WRITE:
                    result = self._execute_file_write_action(substituted_step)
                elif substituted_step.action == ActionType.FILE_READ:
                    result = self._execute_file_read_action(substituted_step)
                elif substituted_step.action == ActionType.FILE_COPY:
                    result = self._execute_file_copy_action(substituted_step)
                elif substituted_step.action == ActionType.SCREENSHOT:
                    result = self._execute_screenshot_action(substituted_step)
                elif substituted_step.action == ActionType.OCR_TEXT:
                    result = self._execute_ocr_action(substituted_step)
                else:
                    raise ValueError(f"Unsupported action type: {substituted_step.action}")
                
                if result:
                    return True  # Step succeeded
                else:
                    raise RuntimeError("Action returned False")
                    
            except Exception as e:
                last_error = e
                
                if attempt < step.retry_attempts:
                    automator_logger.log_step_retry("step_execution", f"execute_{step.action}", 
                                                  step.name, attempt, step.retry_attempts, e)
                    console.print(f"   ⚠️  Retry {attempt}/{step.retry_attempts}: {e}")
                    time.sleep(step.retry_delay)
                else:
                    automator_logger.log_step_failure("step_execution", f"execute_{step.action}", 
                                                    step.name, e)
                    console.print(f"   💥 All retries failed: {e}")
        
        return False
    
    def _substitute_step_variables(self, step: ActionStep) -> ActionStep:
        """Substitute recipe variables in step data."""
        if not self._recipe or not self._recipe.variables:
            return step
        
        # Create a copy of the step with substituted values
        step_dict = step.dict()
        
        # Recursively substitute variables in all string values
        def substitute_recursive(obj):
            if isinstance(obj, str):
                return self._recipe.substitute_variables(obj)
            elif isinstance(obj, dict):
                return {k: substitute_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute_recursive(item) for item in obj]
            else:
                return obj
        
        substituted_dict = substitute_recursive(step_dict)
        return ActionStep(**substituted_dict)
    
    def _execute_launch_action(self, step: ActionStep) -> bool:
        """Execute application launch action."""
        if not step.target.app:
            raise ValueError("Launch action requires app target")
        
        pid, was_running = self.process_provider.launch_application(
            step.target.app, 
            timeout=step.timeout
        )
        
        if step.verify_after and not was_running:
            # Verify app is running
            time.sleep(1)
            return self.process_provider.is_application_running(step.target.app)
        
        return True
    
    def _execute_wait_for_action(self, step: ActionStep) -> bool:
        """Execute wait for UI element action."""
        if step.target.element:
            return self.ui_provider.wait_for_element(
                step.target.element,
                step.target.window,
                timeout=step.timeout,
                app_name=step.target.app
            )
        elif step.target.window:
            return self.ui_provider.wait_for_window(
                step.target.window,
                timeout=step.timeout,
                app_name=step.target.app
            )
        else:
            raise ValueError("Wait_for action requires element or window target")
    
    def _execute_click_action(self, step: ActionStep) -> bool:
        """Execute click UI element action."""
        if not step.target.element:
            raise ValueError("Click action requires element target")
        
        return self.ui_provider.click_element(
            step.target.element,
            step.target.window,
            app_name=step.target.app,
            verify=step.verify_after
        )
    
    def _execute_type_action(self, step: ActionStep) -> bool:
        """Execute type text action."""
        if not step.target.text:
            raise ValueError("Type action requires text target")
        
        return self.ui_provider.type_text(
            step.target.text,
            step.target.element,
            step.target.window,
            app_name=step.target.app,
            verify=step.verify_after
        )
    
    def _execute_hotkey_action(self, step: ActionStep) -> bool:
        """Execute hotkey action."""
        if not step.target.text:
            raise ValueError("Hotkey action requires text target (key combination)")
        
        return self.ui_provider.send_hotkey(
            step.target.text,
            step.target.window,
            app_name=step.target.app
        )
    
    def _execute_verify_action(self, step: ActionStep) -> bool:
        """Execute verification action."""
        if step.target.element and step.target.text:
            # Verify element state
            return self.ui_provider.verify_element_state(
                step.target.element,
                step.target.text,  # Expected state
                step.target.window,
                app_name=step.target.app
            )
        else:
            raise ValueError("Verify action requires element and text (expected state)")
    
    def _execute_read_text_action(self, step: ActionStep) -> bool:
        """Execute read text from element action."""
        if not step.target.element:
            raise ValueError("Read_text action requires element target")
        
        text = self.ui_provider.get_element_text(
            step.target.element,
            step.target.window,
            app_name=step.target.app
        )
        
        # Store result in recipe variables for later use
        if self._recipe and text is not None:
            var_name = f"step_{self._current_step}_result"
            self._recipe.variables[var_name] = text
        
        return text is not None
    
    def _execute_file_write_action(self, step: ActionStep) -> bool:
        """Execute file write action."""
        if not step.target.file_path or not step.target.text:
            raise ValueError("File_write action requires file_path and text targets")
        
        return self.fs_provider.write_file(step.target.file_path, step.target.text)
    
    def _execute_file_read_action(self, step: ActionStep) -> bool:
        """Execute file read action."""
        if not step.target.file_path:
            raise ValueError("File_read action requires file_path target")
        
        try:
            content = self.fs_provider.read_file(step.target.file_path)
            
            # Store result in recipe variables
            if self._recipe:
                var_name = f"step_{self._current_step}_result"
                self._recipe.variables[var_name] = content
            
            return True
        except Exception:
            return False
    
    def _execute_file_copy_action(self, step: ActionStep) -> bool:
        """Execute file copy action."""
        if not step.target.file_path or not step.target.text:
            raise ValueError("File_copy action requires file_path (source) and text (destination)")
        
        return self.fs_provider.copy_file(step.target.file_path, step.target.text)
    
    def _execute_screenshot_action(self, step: ActionStep) -> bool:
        """Execute screenshot action."""
        try:
            import pyautogui
            screenshot_dir = Path("artifacts/screens")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            filename = step.target.file_path or f"screenshot_step_{self._current_step}.png"
            screenshot_path = screenshot_dir / filename
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(screenshot_path))
            
            return True
        except Exception:
            return False
    
    def _execute_ocr_action(self, step: ActionStep) -> bool:
        """Execute OCR text extraction action."""
        if step.target.region:
            # Extract text from screen region
            region = step.target.region
            text = self.ocr_provider.extract_text_from_region(
                region['x'], region['y'], region['width'], region['height']
            )
        elif step.target.file_path:
            # Extract text from image file
            text = self.ocr_provider.extract_text_from_image(step.target.file_path)
        else:
            raise ValueError("OCR action requires region or file_path target")
        
        # Store result in recipe variables
        if self._recipe and text is not None:
            var_name = f"step_{self._current_step}_result"
            self._recipe.variables[var_name] = text
        
        return text is not None
    
    def cleanup(self):
        """Clean up orchestrator resources."""
        self.process_provider.cleanup()
        self.ui_provider.cleanup()


# CLI Commands

@app.command()
def run(
    recipe_path: str = typer.Argument(..., help="Path to recipe YAML file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate recipe without executing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Execute an automation recipe from YAML file."""
    
    if not os.path.exists(recipe_path):
        console.print(f"❌ Recipe file not found: {recipe_path}")
        sys.exit(1)
    
    orchestrator = AutomationOrchestrator()
    
    # Load recipe
    if not orchestrator.load_recipe(recipe_path):
        sys.exit(1)
    
    if dry_run:
        console.print("✅ Recipe validation passed (dry run)")
        return
    
    # Execute recipe
    try:
        success = orchestrator.execute_recipe()
        sys.exit(0 if success else 1)
    finally:
        orchestrator.cleanup()


@app.command()
def validate(recipe_path: str = typer.Argument(..., help="Path to recipe YAML file")):
    """Validate a recipe YAML file without executing it."""
    
    if not os.path.exists(recipe_path):
        console.print(f"❌ Recipe file not found: {recipe_path}")
        sys.exit(1)
    
    try:
        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_data = yaml.safe_load(f)
        
        recipe = load_recipe_from_dict(recipe_data)
        
        console.print(f"✅ Recipe is valid: {recipe.name}")
        
        # Display recipe summary
        table = Table(title="Recipe Summary")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Name", recipe.name)
        table.add_row("Description", recipe.description)
        table.add_row("Version", recipe.version)
        table.add_row("Steps", str(len(recipe.steps)))
        table.add_row("Variables", str(len(recipe.variables)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Recipe validation failed: {e}")
        sys.exit(1)


@app.command()
def list_providers():
    """List available automation providers and their status."""
    
    orchestrator = AutomationOrchestrator()
    
    table = Table(title="Automation Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="green")
    
    table.add_row("Process", "✅ Available", "Application lifecycle management")
    table.add_row("UI", "✅ Available", "pywinauto UIA backend")
    table.add_row("FileSystem", "✅ Available", "File operations with security")
    
    # Check OCR availability
    ocr_status = "✅ Available" if orchestrator.ocr_provider.is_tesseract_available() else "⚠️  Limited (no tesseract)"
    table.add_row("OCR", ocr_status, "Text extraction with pytesseract")
    
    console.print(table)


@app.command()
def version():
    """Show version information."""
    console.print("Windows Desktop Automator v1.0")
    console.print("Built with Python 3.11, pywinauto, and Typer")


if __name__ == "__main__":
    app()

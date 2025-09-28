"""
Centralized logging system with JSON output and screenshot capture.
Implements structured logging for automation steps with failure screenshots.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pyautogui
from loguru import logger


class AutomatorLogger:
    """Centralized logger with JSON output and screenshot capture on failure."""
    
    def __init__(self, artifacts_dir: str = "./artifacts"):
        """Initialize logger with artifacts directory."""
        self.artifacts_dir = Path(artifacts_dir)
        self.logs_dir = self.artifacts_dir / "logs"
        self.screens_dir = self.artifacts_dir / "screens"
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.screens_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure loguru for structured JSON logging
        log_file = self.logs_dir / f"automator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logger.remove()  # Remove default handler
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            serialize=True,  # JSON format
            level="INFO"
        )
        logger.add(
            lambda msg: print(msg, end=""),  # Console output
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO"
        )
        
        self._session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._step_counter = 0
    
    def log_step_start(self, action: str, target: str, **kwargs) -> str:
        """Log the start of an automation step."""
        self._step_counter += 1
        step_id = f"{self._session_id}_{self._step_counter:03d}"
        
        log_data = {
            "step_id": step_id,
            "action": action,
            "target": target,
            "phase": "START",
            "timestamp": datetime.now().isoformat(),
            "details": kwargs
        }
        
        logger.info(f"Step {self._step_counter}: {action} on {target}", extra={"structured": log_data})
        return step_id
    
    def log_step_success(self, step_id: str, action: str, target: str, result: Any = None, **kwargs):
        """Log successful completion of an automation step."""
        log_data = {
            "step_id": step_id,
            "action": action,
            "target": target,
            "phase": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "result": str(result) if result is not None else None,
            "details": kwargs
        }
        
        logger.success(f"Step completed: {action} on {target}", extra={"structured": log_data})
    
    def log_step_failure(self, step_id: str, action: str, target: str, error: Exception, **kwargs):
        """Log failure of an automation step with screenshot."""
        screenshot_path = self._capture_failure_screenshot(step_id, action)
        
        log_data = {
            "step_id": step_id,
            "action": action,
            "target": target,
            "phase": "FAILURE",
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "screenshot": str(screenshot_path) if screenshot_path else None,
            "details": kwargs
        }
        
        logger.error(f"Step failed: {action} on {target} - {error}", extra={"structured": log_data})
    
    def log_step_retry(self, step_id: str, action: str, target: str, attempt: int, max_attempts: int, error: Exception):
        """Log retry attempt for an automation step."""
        log_data = {
            "step_id": step_id,
            "action": action,
            "target": target,
            "phase": "RETRY",
            "timestamp": datetime.now().isoformat(),
            "attempt": attempt,
            "max_attempts": max_attempts,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        logger.warning(f"Retrying step ({attempt}/{max_attempts}): {action} on {target}", extra={"structured": log_data})
    
    def log_recipe_start(self, recipe_name: str, recipe_path: str):
        """Log the start of recipe execution."""
        log_data = {
            "event": "RECIPE_START",
            "recipe_name": recipe_name,
            "recipe_path": recipe_path,
            "session_id": self._session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Starting recipe: {recipe_name}", extra={"structured": log_data})
    
    def log_recipe_complete(self, recipe_name: str, total_steps: int, duration: float):
        """Log successful completion of recipe."""
        log_data = {
            "event": "RECIPE_COMPLETE",
            "recipe_name": recipe_name,
            "session_id": self._session_id,
            "total_steps": total_steps,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.success(f"Recipe completed: {recipe_name} ({total_steps} steps in {duration:.2f}s)", extra={"structured": log_data})
    
    def log_recipe_failure(self, recipe_name: str, failed_step: int, error: Exception):
        """Log recipe failure."""
        log_data = {
            "event": "RECIPE_FAILURE",
            "recipe_name": recipe_name,
            "session_id": self._session_id,
            "failed_step": failed_step,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.error(f"Recipe failed: {recipe_name} at step {failed_step}", extra={"structured": log_data})
    
    def _capture_failure_screenshot(self, step_id: str, action: str) -> Optional[Path]:
        """Capture screenshot on failure for debugging."""
        try:
            screenshot_filename = f"failure_{step_id}_{action.replace(' ', '_')}.png"
            screenshot_path = self.screens_dir / screenshot_filename
            
            # Capture screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(str(screenshot_path))
            
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def get_session_id(self) -> str:
        """Get current logging session ID."""
        return self._session_id


# Global logger instance
automator_logger = AutomatorLogger()

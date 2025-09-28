"""
Process management provider for launching, controlling, and monitoring applications.
Handles application lifecycle with idempotency and process state detection.
"""

import os
import subprocess
import time
from typing import Dict, List, Optional, Tuple

import psutil
import pywinauto
from pywinauto.application import Application

from automator.core.logger import automator_logger


class ProcessProvider:
    """Provider for managing application processes and lifecycle."""
    
    def __init__(self):
        """Initialize process provider."""
        self._launched_processes: Dict[str, int] = {}  # app_name -> pid
        self._applications: Dict[str, Application] = {}  # app_name -> pywinauto app
    
    def launch_application(self, app_path: str, args: List[str] = None, working_dir: str = None, 
                          wait_for_ready: bool = True, timeout: int = 30) -> Tuple[int, bool]:
        """
        Launch application with idempotency checks.
        
        Args:
            app_path: Path to executable or app name
            args: Command line arguments
            working_dir: Working directory for the process
            wait_for_ready: Wait for app to be ready for automation
            timeout: Timeout for app readiness
        
        Returns:
            Tuple of (process_id, was_already_running)
        """
        step_id = automator_logger.log_step_start("launch_application", app_path, 
                                                  args=args, working_dir=working_dir)
        
        try:
            app_name = os.path.basename(app_path)
            
            # Check if application is already running
            existing_pid = self._find_existing_process(app_name)
            if existing_pid:
                automator_logger.log_step_success(step_id, "launch_application", app_path, 
                                                result=f"Already running (PID: {existing_pid})")
                self._launched_processes[app_name] = existing_pid
                return existing_pid, True
            
            # Launch new process
            cmd = [app_path] + (args or [])
            process = subprocess.Popen(cmd, cwd=working_dir)
            
            # Wait for process to start
            time.sleep(2)  # Brief wait for process initialization
            
            if not process.poll() is None:
                raise RuntimeError(f"Process exited immediately with code {process.returncode}")
            
            # Find the actual PID (subprocess might spawn child processes)
            actual_pid = self._find_process_by_name(app_name)
            if not actual_pid:
                actual_pid = process.pid
            
            self._launched_processes[app_name] = actual_pid
            
            # Wait for application to be ready for automation
            if wait_for_ready:
                self._wait_for_application_ready(app_name, actual_pid, timeout)
            
            automator_logger.log_step_success(step_id, "launch_application", app_path, 
                                            result=f"Launched (PID: {actual_pid})")
            return actual_pid, False
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "launch_application", app_path, e)
            raise
    
    def bring_to_foreground(self, app_name: str, window_title: str = None) -> bool:
        """
        Bring application window to foreground.
        
        Args:
            app_name: Application name or PID
            window_title: Specific window title (optional)
        
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("bring_to_foreground", app_name, 
                                                  window_title=window_title)
        
        try:
            app = self._get_or_connect_application(app_name)
            
            if window_title:
                window = app.window(title_re=f".*{window_title}.*")
            else:
                window = app.top_window()
            
            # Restore if minimized
            if window.is_minimized():
                window.restore()
            
            # Bring to foreground
            window.set_focus()
            
            automator_logger.log_step_success(step_id, "bring_to_foreground", app_name)
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "bring_to_foreground", app_name, e)
            return False
    
    def terminate_application(self, app_name: str, force: bool = False, timeout: int = 10) -> bool:
        """
        Terminate application gracefully or forcefully.
        
        Args:
            app_name: Application name
            force: Force termination if graceful fails
            timeout: Timeout for graceful termination
        
        Returns:
            True if terminated successfully
        """
        step_id = automator_logger.log_step_start("terminate_application", app_name, 
                                                  force=force, timeout=timeout)
        
        try:
            pid = self._launched_processes.get(app_name)
            if not pid:
                pid = self._find_process_by_name(app_name)
                if not pid:
                    automator_logger.log_step_success(step_id, "terminate_application", app_name,
                                                    result="Not running")
                    return True
            
            process = psutil.Process(pid)
            
            if not force:
                # Graceful termination
                process.terminate()
                try:
                    process.wait(timeout=timeout)
                except psutil.TimeoutExpired:
                    if force:
                        process.kill()
                        process.wait(timeout=5)
                    else:
                        raise RuntimeError(f"Process did not terminate within {timeout} seconds")
            else:
                # Force kill
                process.kill()
                process.wait(timeout=5)
            
            # Clean up tracking
            if app_name in self._launched_processes:
                del self._launched_processes[app_name]
            if app_name in self._applications:
                del self._applications[app_name]
            
            automator_logger.log_step_success(step_id, "terminate_application", app_name)
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "terminate_application", app_name, e)
            return False
    
    def is_application_running(self, app_name: str) -> bool:
        """Check if application is currently running."""
        try:
            pid = self._launched_processes.get(app_name)
            if pid:
                return psutil.pid_exists(pid)
            return self._find_process_by_name(app_name) is not None
        except Exception:
            return False
    
    def get_application_windows(self, app_name: str) -> List[Dict[str, str]]:
        """Get list of windows for the application."""
        try:
            app = self._get_or_connect_application(app_name)
            windows = []
            
            for window in app.windows():
                try:
                    windows.append({
                        'title': window.window_text(),
                        'class_name': window.class_name(),
                        'control_id': str(window.control_id()),
                        'is_visible': window.is_visible(),
                        'is_enabled': window.is_enabled()
                    })
                except Exception:
                    continue  # Skip windows that can't be accessed
            
            return windows
        except Exception:
            return []
    
    def _find_existing_process(self, app_name: str) -> Optional[int]:
        """Find existing process by name."""
        try:
            for process in psutil.process_iter(['pid', 'name']):
                if process.info['name'].lower() == app_name.lower():
                    return process.info['pid']
        except Exception:
            pass
        return None
    
    def _find_process_by_name(self, app_name: str) -> Optional[int]:
        """Find process PID by application name."""
        try:
            for process in psutil.process_iter(['pid', 'name']):
                if process.info['name'].lower() == app_name.lower():
                    return process.info['pid']
        except Exception:
            pass
        return None
    
    def _wait_for_application_ready(self, app_name: str, pid: int, timeout: int):
        """Wait for application to be ready for automation."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect with pywinauto
                app = Application().connect(process=pid)
                # Try to get top window
                app.top_window()
                # If we get here, app is ready
                self._applications[app_name] = app
                return
            except Exception:
                time.sleep(1)
        
        raise RuntimeError(f"Application {app_name} not ready for automation within {timeout} seconds")
    
    def _get_or_connect_application(self, app_name: str) -> Application:
        """Get existing application connection or create new one."""
        if app_name in self._applications:
            return self._applications[app_name]
        
        # Try to connect by PID first
        pid = self._launched_processes.get(app_name)
        if pid and psutil.pid_exists(pid):
            try:
                app = Application().connect(process=pid)
                self._applications[app_name] = app
                return app
            except Exception:
                pass
        
        # Try to connect by name
        try:
            app = Application().connect(path=app_name)
            self._applications[app_name] = app
            return app
        except Exception:
            pass
        
        # Try to find and connect to any matching process
        pid = self._find_process_by_name(app_name)
        if pid:
            app = Application().connect(process=pid)
            self._applications[app_name] = app
            return app
        
        raise RuntimeError(f"Cannot connect to application: {app_name}")
    
    def cleanup(self):
        """Clean up provider resources."""
        self._applications.clear()
        self._launched_processes.clear()

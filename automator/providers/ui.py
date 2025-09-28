"""
UI automation provider using pywinauto with UIA backend.
Implements wait→act→verify pattern with intelligent element location and fallback strategies.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union

import pywinauto
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.findwindows import ElementNotFoundError
import uiautomation as auto

from automator.core.dsl import ElementSelector, WindowSelector
from automator.core.logger import automator_logger


class UIProvider:
    """Provider for UI automation using pywinauto with UIA backend."""
    
    def __init__(self):
        """Initialize UI provider."""
        # Force UIA backend
        pywinauto.backend = 'uia'
        self._applications: Dict[str, Application] = {}
        self._element_cache: Dict[str, UIAWrapper] = {}
        self._last_screenshot_path: Optional[str] = None
    
    def wait_for_window(self, window_selector: WindowSelector, timeout: int = 10, 
                       app_name: str = None) -> bool:
        """
        Wait for window to appear and be ready.
        
        Args:
            window_selector: Window selector criteria
            timeout: Timeout in seconds
            app_name: Application name for connection
            
        Returns:
            True if window found and ready
        """
        step_id = automator_logger.log_step_start("wait_for_window", str(window_selector), 
                                                  timeout=timeout, app_name=app_name)
        
        start_time = time.time()
        last_error = None
        
        while time.time() - start_time < timeout:
            try:
                window = self._find_window(window_selector, app_name)
                if window and window.is_visible():
                    # Additional readiness checks
                    if self._is_window_ready(window):
                        automator_logger.log_step_success(step_id, "wait_for_window", str(window_selector))
                        return True
                
                time.sleep(0.5)
                
            except Exception as e:
                last_error = e
                time.sleep(0.5)
        
        error = last_error or TimeoutError(f"Window not found within {timeout} seconds")
        automator_logger.log_step_failure(step_id, "wait_for_window", str(window_selector), error)
        return False
    
    def wait_for_element(self, element_selector: ElementSelector, window_selector: WindowSelector = None,
                        timeout: int = 10, app_name: str = None) -> bool:
        """
        Wait for UI element to be available and ready.
        
        Args:
            element_selector: Element selector criteria
            window_selector: Parent window selector
            timeout: Timeout in seconds
            app_name: Application name
            
        Returns:
            True if element found and ready
        """
        step_id = automator_logger.log_step_start("wait_for_element", str(element_selector), 
                                                  timeout=timeout, window_selector=str(window_selector))
        
        start_time = time.time()
        last_error = None
        
        while time.time() - start_time < timeout:
            try:
                element = self._find_element(element_selector, window_selector, app_name)
                if element and element.is_visible() and element.is_enabled():
                    automator_logger.log_step_success(step_id, "wait_for_element", str(element_selector))
                    return True
                
                time.sleep(0.5)
                
            except Exception as e:
                last_error = e
                time.sleep(0.5)
        
        error = last_error or TimeoutError(f"Element not found within {timeout} seconds")
        automator_logger.log_step_failure(step_id, "wait_for_element", str(element_selector), error)
        return False
    
    def click_element(self, element_selector: ElementSelector, window_selector: WindowSelector = None,
                     app_name: str = None, click_type: str = "left", verify: bool = True) -> bool:
        """
        Click on UI element.
        
        Args:
            element_selector: Element selector criteria
            window_selector: Parent window selector
            app_name: Application name
            click_type: Type of click (left, right, double)
            verify: Verify click success
            
        Returns:
            True if click successful
        """
        step_id = automator_logger.log_step_start("click_element", str(element_selector), 
                                                  click_type=click_type, verify=verify)
        
        try:
            element = self._find_element(element_selector, window_selector, app_name)
            if not element:
                raise ElementNotFoundError(f"Element not found: {element_selector}")
            
            # Ensure element is ready for interaction
            if not element.is_visible() or not element.is_enabled():
                raise RuntimeError(f"Element not ready for interaction: {element_selector}")
            
            # Scroll element into view if needed
            try:
                element.scroll_to_view()
            except Exception:
                pass  # Scroll might not be supported
            
            # Perform click based on type
            if click_type == "left":
                element.click_input()
            elif click_type == "right":
                element.right_click_input()
            elif click_type == "double":
                element.double_click_input()
            else:
                raise ValueError(f"Invalid click type: {click_type}")
            
            # Brief wait for UI to respond
            time.sleep(0.2)
            
            # Verify click if requested
            if verify:
                self._verify_click_success(element, element_selector)
            
            automator_logger.log_step_success(step_id, "click_element", str(element_selector))
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "click_element", str(element_selector), e)
            return False
    
    def type_text(self, text: str, element_selector: ElementSelector = None, 
                 window_selector: WindowSelector = None, app_name: str = None,
                 clear_first: bool = True, verify: bool = True) -> bool:
        """
        Type text into element or active window.
        
        Args:
            text: Text to type
            element_selector: Target element (None for active window)
            window_selector: Parent window selector
            app_name: Application name
            clear_first: Clear existing text first
            verify: Verify text was entered
            
        Returns:
            True if typing successful
        """
        step_id = automator_logger.log_step_start("type_text", f"'{text}' -> {element_selector}", 
                                                  clear_first=clear_first, verify=verify)
        
        try:
            element = None
            if element_selector:
                element = self._find_element(element_selector, window_selector, app_name)
                if not element:
                    raise ElementNotFoundError(f"Element not found: {element_selector}")
                
                # Focus the element
                element.set_focus()
                
                # Clear existing text if requested
                if clear_first:
                    element.select_all()
                    time.sleep(0.1)
            
            # Type the text
            if element:
                element.type_keys(text, with_spaces=True)
            else:
                # Type to active window
                pywinauto.keyboard.send_keys(text)
            
            # Brief wait for UI to respond
            time.sleep(0.2)
            
            # Verify text was entered if requested
            if verify and element:
                self._verify_text_input(element, text, element_selector)
            
            automator_logger.log_step_success(step_id, "type_text", f"'{text}' -> {element_selector}")
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "type_text", f"'{text}' -> {element_selector}", e)
            return False
    
    def send_hotkey(self, keys: str, window_selector: WindowSelector = None, 
                   app_name: str = None) -> bool:
        """
        Send hotkey combination.
        
        Args:
            keys: Key combination (e.g., "ctrl+c", "alt+f4")
            window_selector: Target window
            app_name: Application name
            
        Returns:
            True if hotkey sent successfully
        """
        step_id = automator_logger.log_step_start("send_hotkey", keys, 
                                                  window_selector=str(window_selector))
        
        try:
            # Focus target window if specified
            if window_selector:
                window = self._find_window(window_selector, app_name)
                if window:
                    window.set_focus()
                    time.sleep(0.1)
            
            # Send hotkey
            pywinauto.keyboard.send_keys(keys)
            
            # Brief wait for action to complete
            time.sleep(0.3)
            
            automator_logger.log_step_success(step_id, "send_hotkey", keys)
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "send_hotkey", keys, e)
            return False
    
    def get_element_text(self, element_selector: ElementSelector, window_selector: WindowSelector = None,
                        app_name: str = None) -> Optional[str]:
        """
        Get text content from UI element.
        
        Args:
            element_selector: Element selector criteria
            window_selector: Parent window selector
            app_name: Application name
            
        Returns:
            Element text content or None if not found
        """
        step_id = automator_logger.log_step_start("get_element_text", str(element_selector))
        
        try:
            element = self._find_element(element_selector, window_selector, app_name)
            if not element:
                raise ElementNotFoundError(f"Element not found: {element_selector}")
            
            # Try different methods to get text
            text = None
            try:
                text = element.window_text()
            except Exception:
                try:
                    text = element.get_value()
                except Exception:
                    try:
                        text = element.element_info.name
                    except Exception:
                        pass
            
            if text is None:
                text = ""
            
            automator_logger.log_step_success(step_id, "get_element_text", str(element_selector), 
                                            result=f"'{text}'")
            return text
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "get_element_text", str(element_selector), e)
            return None
    
    def verify_element_state(self, element_selector: ElementSelector, expected_state: str,
                           window_selector: WindowSelector = None, app_name: str = None) -> bool:
        """
        Verify element is in expected state.
        
        Args:
            element_selector: Element selector criteria
            expected_state: Expected state (visible, enabled, focused, selected)
            window_selector: Parent window selector
            app_name: Application name
            
        Returns:
            True if element is in expected state
        """
        step_id = automator_logger.log_step_start("verify_element_state", 
                                                  f"{element_selector} -> {expected_state}")
        
        try:
            element = self._find_element(element_selector, window_selector, app_name)
            if not element:
                raise ElementNotFoundError(f"Element not found: {element_selector}")
            
            # Check state based on expected_state
            result = False
            if expected_state == "visible":
                result = element.is_visible()
            elif expected_state == "enabled":
                result = element.is_enabled()
            elif expected_state == "focused":
                result = element.has_focus()
            elif expected_state == "selected":
                try:
                    result = element.is_selected()
                except Exception:
                    result = False
            else:
                raise ValueError(f"Invalid expected state: {expected_state}")
            
            if result:
                automator_logger.log_step_success(step_id, "verify_element_state", 
                                                f"{element_selector} -> {expected_state}")
            else:
                error = RuntimeError(f"Element not in expected state: {expected_state}")
                automator_logger.log_step_failure(step_id, "verify_element_state", 
                                                f"{element_selector} -> {expected_state}", error)
            
            return result
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "verify_element_state", 
                                            f"{element_selector} -> {expected_state}", e)
            return False
    
    def _find_window(self, window_selector: WindowSelector, app_name: str = None) -> Optional[UIAWrapper]:
        """Find window based on selector criteria."""
        try:
            app = None
            
            # Try to get existing app connection
            if app_name and app_name in self._applications:
                app = self._applications[app_name]
            elif app_name:
                # Try to connect to app
                try:
                    app = Application(backend='uia').connect(path=app_name)
                    self._applications[app_name] = app
                except Exception:
                    pass
            
            # Search criteria
            search_criteria = {}
            if window_selector.name:
                search_criteria['title'] = window_selector.name
            if window_selector.class_name:
                search_criteria['class_name'] = window_selector.class_name
            if window_selector.process_id:
                search_criteria['process'] = window_selector.process_id
            
            # Find window
            if app:
                return app.window(**search_criteria)
            else:
                # Find any matching window
                return Application(backend='uia').connect(**search_criteria).top_window()
                
        except Exception:
            return None
    
    def _find_element(self, element_selector: ElementSelector, window_selector: WindowSelector = None,
                     app_name: str = None) -> Optional[UIAWrapper]:
        """Find element with fallback strategies."""
        try:
            # Get parent window
            window = None
            if window_selector:
                window = self._find_window(window_selector, app_name)
            elif app_name and app_name in self._applications:
                window = self._applications[app_name].top_window()
            
            if not window:
                # Try desktop if no window found
                window = Application(backend='uia').connect(path='explorer.exe').top_window()
            
            # Build search criteria with entropy-based ordering
            search_criteria = []
            
            # Primary criteria (high entropy)
            if element_selector.automation_id:
                search_criteria.append({'auto_id': element_selector.automation_id})
            
            # Secondary criteria (medium entropy)
            if element_selector.control_type and element_selector.name:
                search_criteria.append({
                    'control_type': element_selector.control_type,
                    'title': element_selector.name
                })
            
            if element_selector.class_name and element_selector.name:
                search_criteria.append({
                    'class_name': element_selector.class_name,
                    'title': element_selector.name
                })
            
            # Fallback criteria (lower entropy)
            if element_selector.name:
                search_criteria.append({'title': element_selector.name})
            
            if element_selector.control_type:
                search_criteria.append({'control_type': element_selector.control_type})
            
            # Try each criteria set in order
            for criteria in search_criteria:
                try:
                    elements = window.descendants(**criteria)
                    if elements:
                        # Use index if specified
                        index = element_selector.index or 0
                        if index < len(elements):
                            return elements[index]
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _is_window_ready(self, window: UIAWrapper) -> bool:
        """Check if window is ready for automation."""
        try:
            return (window.is_visible() and 
                   window.is_enabled() and 
                   not window.is_minimized())
        except Exception:
            return False
    
    def _verify_click_success(self, element: UIAWrapper, element_selector: ElementSelector):
        """Verify click was successful."""
        # Basic verification - element should still be accessible
        try:
            element.is_visible()  # Just check accessibility
        except Exception:
            raise RuntimeError("Click verification failed - element became inaccessible")
    
    def _verify_text_input(self, element: UIAWrapper, expected_text: str, 
                          element_selector: ElementSelector):
        """Verify text input was successful."""
        try:
            time.sleep(0.5)  # Wait for UI to update
            actual_text = element.window_text() or element.get_value() or ""
            
            # Check if expected text is in actual text (partial match)
            if expected_text not in actual_text:
                raise RuntimeError(f"Text verification failed. Expected: '{expected_text}', Got: '{actual_text}'")
            
        except Exception as e:
            if "verification failed" in str(e):
                raise
            # If we can't verify, log warning but don't fail
            automator_logger.log_step_retry("text_verify", "verify_text_input", str(element_selector), 1, 1, e)
    
    def cleanup(self):
        """Clean up provider resources."""
        self._applications.clear()
        self._element_cache.clear()

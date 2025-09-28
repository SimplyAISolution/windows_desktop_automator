"""
OCR (Optical Character Recognition) provider with pytesseract fallback.
Provides text extraction from screen regions and images when UI automation fails.
"""

import os
import tempfile
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageGrab
import cv2
import numpy as np

from automator.core.logger import automator_logger


class OCRProvider:
    """Provider for optical character recognition with fallback capabilities."""
    
    def __init__(self, tesseract_path: str = None):
        """
        Initialize OCR provider.
        
        Args:
            tesseract_path: Path to tesseract executable (auto-detect if None)
        """
        self._tesseract_available = False
        self._tesseract_path = tesseract_path
        
        # Try to initialize tesseract
        try:
            import pytesseract
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Test tesseract availability
            test_image = Image.new('RGB', (100, 30), color='white')
            pytesseract.image_to_string(test_image)
            self._tesseract_available = True
            
        except Exception as e:
            automator_logger.log_step_failure("ocr_init", "initialize_tesseract", "tesseract", e)
    
    def extract_text_from_region(self, x: int, y: int, width: int, height: int,
                                preprocessing: str = "default") -> Optional[str]:
        """
        Extract text from screen region using OCR.
        
        Args:
            x: Region X coordinate
            y: Region Y coordinate  
            width: Region width
            height: Region height
            preprocessing: Image preprocessing method
            
        Returns:
            Extracted text or None if failed
        """
        step_id = automator_logger.log_step_start("extract_text_from_region", 
                                                  f"({x}, {y}, {width}, {height})",
                                                  preprocessing=preprocessing)
        
        try:
            # Capture screenshot of region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Apply preprocessing
            processed_image = self._preprocess_image(screenshot, preprocessing)
            
            # Extract text
            text = self._extract_text_from_image(processed_image)
            
            automator_logger.log_step_success(step_id, "extract_text_from_region", 
                                            f"({x}, {y}, {width}, {height})",
                                            result=f"'{text}'")
            return text
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "extract_text_from_region", 
                                            f"({x}, {y}, {width}, {height})", e)
            return None
    
    def extract_text_from_image(self, image_path: str, preprocessing: str = "default") -> Optional[str]:
        """
        Extract text from image file using OCR.
        
        Args:
            image_path: Path to image file
            preprocessing: Image preprocessing method
            
        Returns:
            Extracted text or None if failed
        """
        step_id = automator_logger.log_step_start("extract_text_from_image", image_path,
                                                  preprocessing=preprocessing)
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Apply preprocessing
            processed_image = self._preprocess_image(image, preprocessing)
            
            # Extract text
            text = self._extract_text_from_image(processed_image)
            
            automator_logger.log_step_success(step_id, "extract_text_from_image", image_path,
                                            result=f"'{text}'")
            return text
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "extract_text_from_image", image_path, e)
            return None
    
    def find_text_in_region(self, text: str, x: int, y: int, width: int, height: int,
                           case_sensitive: bool = False, whole_words: bool = False) -> List[Dict[str, any]]:
        """
        Find specific text in screen region.
        
        Args:
            text: Text to search for
            x: Region X coordinate
            y: Region Y coordinate
            width: Region width
            height: Region height
            case_sensitive: Case sensitive search
            whole_words: Match whole words only
            
        Returns:
            List of text locations with coordinates
        """
        step_id = automator_logger.log_step_start("find_text_in_region", 
                                                  f"'{text}' in ({x}, {y}, {width}, {height})",
                                                  case_sensitive=case_sensitive, whole_words=whole_words)
        
        try:
            # Get detailed OCR data with coordinates
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            processed_image = self._preprocess_image(screenshot, "default")
            
            ocr_data = self._get_ocr_data_with_coordinates(processed_image)
            
            # Search for text matches
            matches = []
            search_text = text if case_sensitive else text.lower()
            
            for item in ocr_data:
                item_text = item['text'] if case_sensitive else item['text'].lower()
                
                if whole_words:
                    # Match whole words
                    import re
                    pattern = r'\b' + re.escape(search_text) + r'\b'
                    if re.search(pattern, item_text):
                        matches.append({
                            'text': item['text'],
                            'x': x + item['left'],
                            'y': y + item['top'],
                            'width': item['width'],
                            'height': item['height'],
                            'confidence': item['conf']
                        })
                else:
                    # Substring match
                    if search_text in item_text:
                        matches.append({
                            'text': item['text'],
                            'x': x + item['left'],
                            'y': y + item['top'],
                            'width': item['width'],
                            'height': item['height'],
                            'confidence': item['conf']
                        })
            
            automator_logger.log_step_success(step_id, "find_text_in_region", 
                                            f"'{text}' in ({x}, {y}, {width}, {height})",
                                            result=f"{len(matches)} matches")
            return matches
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "find_text_in_region", 
                                            f"'{text}' in ({x}, {y}, {width}, {height})", e)
            return []
    
    def extract_text_from_window(self, window_title: str, preprocessing: str = "default") -> Optional[str]:
        """
        Extract text from entire window using OCR.
        
        Args:
            window_title: Window title to capture
            preprocessing: Image preprocessing method
            
        Returns:
            Extracted text or None if failed
        """
        step_id = automator_logger.log_step_start("extract_text_from_window", window_title,
                                                  preprocessing=preprocessing)
        
        try:
            # Find window and get its bounds
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(window_title)
            
            if not windows:
                raise RuntimeError(f"Window not found: {window_title}")
            
            window = windows[0]
            
            # Capture window screenshot
            screenshot = ImageGrab.grab(bbox=(window.left, window.top, window.right, window.bottom))
            
            # Apply preprocessing
            processed_image = self._preprocess_image(screenshot, preprocessing)
            
            # Extract text
            text = self._extract_text_from_image(processed_image)
            
            automator_logger.log_step_success(step_id, "extract_text_from_window", window_title,
                                            result=f"'{text[:100]}...' ({len(text)} chars)")
            return text
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "extract_text_from_window", window_title, e)
            return None
    
    def is_tesseract_available(self) -> bool:
        """Check if tesseract OCR is available."""
        return self._tesseract_available
    
    def _preprocess_image(self, image: Image.Image, method: str) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            method: Preprocessing method
            
        Returns:
            Processed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            if method == "default":
                # Basic preprocessing
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
            elif method == "high_contrast":
                # High contrast preprocessing
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                cv2.THRESH_BINARY, 11, 2)
                
            elif method == "denoise":
                # Noise reduction preprocessing
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                denoised = cv2.medianBlur(gray, 3)
                processed = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
            elif method == "scale_up":
                # Scale up small text
                gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                processed = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
            else:
                # No preprocessing
                processed = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Convert back to PIL
            return Image.fromarray(processed)
            
        except Exception:
            # Return original image if preprocessing fails
            return image
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from PIL Image using available OCR methods."""
        if self._tesseract_available:
            return self._extract_text_with_tesseract(image)
        else:
            # Fallback to basic text extraction (limited functionality)
            return self._extract_text_fallback(image)
    
    def _extract_text_with_tesseract(self, image: Image.Image) -> str:
        """Extract text using pytesseract."""
        try:
            import pytesseract
            
            # Configure tesseract for better accuracy
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=config)
            
            # Clean up text
            return text.strip()
            
        except Exception as e:
            raise RuntimeError(f"Tesseract OCR failed: {e}")
    
    def _get_ocr_data_with_coordinates(self, image: Image.Image) -> List[Dict[str, any]]:
        """Get OCR data with bounding box coordinates."""
        if not self._tesseract_available:
            return []
        
        try:
            import pytesseract
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Filter and format data
            results = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:  # Confidence threshold
                    text = data['text'][i].strip()
                    if text:  # Only include non-empty text
                        results.append({
                            'text': text,
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
                            'conf': float(data['conf'][i])
                        })
            
            return results
            
        except Exception:
            return []
    
    def _extract_text_fallback(self, image: Image.Image) -> str:
        """Basic fallback OCR when tesseract is not available."""
        # This is a very limited fallback - mainly returns empty string
        # In a real implementation, you might use alternative OCR services
        # like cloud APIs (Google Vision, Azure Computer Vision, etc.)
        return ""
    
    def save_debug_image(self, image: Image.Image, filename: str) -> bool:
        """Save image for debugging OCR issues."""
        try:
            debug_dir = os.path.join(os.getcwd(), "artifacts", "ocr_debug")
            os.makedirs(debug_dir, exist_ok=True)
            
            debug_path = os.path.join(debug_dir, filename)
            image.save(debug_path)
            
            return True
        except Exception:
            return False

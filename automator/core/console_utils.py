"""
Console utilities for safe Unicode output with ASCII fallbacks.
Handles Windows Command Prompt Unicode limitations gracefully.
"""

import sys
from typing import Any
from rich.console import Console as RichConsole


# Emoji to ASCII fallback mapping
EMOJI_FALLBACKS = {
    '✅': '[OK]',
    '❌': '[ERROR]',
    '🚀': '>>', 
    '📍': '*',
    '🎉': '[SUCCESS]',
    '💥': '[FAILED]',
    '⚠️': '[WARNING]',
    '💡': '[INFO]',
}


class SafeConsole:
    """
    Console wrapper that provides safe Unicode output with ASCII fallbacks.
    
    This class wraps Rich Console and automatically handles Unicode encoding
    errors by falling back to ASCII alternatives when emojis can't be displayed.
    """
    
    def __init__(self, force_ascii: bool = False):
        """
        Initialize SafeConsole.
        
        Args:
            force_ascii: If True, always use ASCII fallbacks instead of emojis
        """
        self._console = RichConsole()
        self._force_ascii = force_ascii
        self._unicode_supported = self._test_unicode_support()
    
    def _test_unicode_support(self) -> bool:
        """
        Test if the current console supports Unicode emoji display.
        
        Returns:
            True if Unicode emojis are supported, False otherwise
        """
        if self._force_ascii:
            return False
            
        try:
            # Try to encode a test emoji
            test_emoji = '✅'
            if sys.stdout.encoding:
                test_emoji.encode(sys.stdout.encoding)
            return True
        except (UnicodeEncodeError, AttributeError, LookupError):
            return False
    
    def _safe_text(self, text: str) -> str:
        """
        Convert text with emojis to a safe version with ASCII fallbacks if needed.
        
        Args:
            text: Text that may contain emoji characters
            
        Returns:
            Safe text with ASCII fallbacks if Unicode is not supported
        """
        if self._unicode_supported:
            return text
            
        # Replace emojis with ASCII fallbacks
        safe_text = text
        for emoji, fallback in EMOJI_FALLBACKS.items():
            safe_text = safe_text.replace(emoji, fallback)
        
        return safe_text
    
    def print(self, *args, **kwargs):
        """
        Safe print method that handles Unicode issues gracefully.
        
        Args:
            *args: Arguments to pass to console.print()
            **kwargs: Keyword arguments to pass to console.print()
        """
        try:
            # Convert all string arguments to safe versions
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_args.append(self._safe_text(arg))
                else:
                    safe_args.append(arg)
            
            self._console.print(*safe_args, **kwargs)
            
        except UnicodeEncodeError:
            # Last resort: force ASCII conversion
            ascii_args = []
            for arg in args:
                if isinstance(arg, str):
                    # Force ASCII conversion for all emojis
                    ascii_text = arg
                    for emoji, fallback in EMOJI_FALLBACKS.items():
                        ascii_text = ascii_text.replace(emoji, fallback)
                    ascii_args.append(ascii_text)
                else:
                    ascii_args.append(str(arg))
            
            self._console.print(*ascii_args, **kwargs)


# Global instance for easy importing
console = SafeConsole()


def safe_print(text: str, force_ascii: bool = False) -> str:
    """
    Utility function to convert text with emojis to safe ASCII alternatives.
    
    Args:
        text: Text that may contain emoji characters
        force_ascii: If True, always convert emojis to ASCII
        
    Returns:
        Safe text that can be displayed in any console
    """
    if not force_ascii:
        try:
            # Test if we can encode this text
            if sys.stdout.encoding:
                text.encode(sys.stdout.encoding)
            return text
        except (UnicodeEncodeError, AttributeError, LookupError):
            pass
    
    # Convert to ASCII fallbacks
    safe_text = text
    for emoji, fallback in EMOJI_FALLBACKS.items():
        safe_text = safe_text.replace(emoji, fallback)
    
    return safe_text
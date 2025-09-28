#!/usr/bin/env python3
"""
CLI entry point for Windows Desktop Automator.
Run automation recipes from the command line.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from automator.core.main import app

if __name__ == "__main__":
    app()
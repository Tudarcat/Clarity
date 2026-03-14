"""
Entry point for Clarity Agent CLI.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.main import app

if __name__ == "__main__":
    app()

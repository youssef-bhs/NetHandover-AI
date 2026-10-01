#!/usr/bin/env python
"""Launcher script for the FastAPI backend."""
import os
import sys

# Ensure we're using the correct Python path
# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uvicorn import run

if __name__ == "__main__":
    run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )

"""Main entry point for the ESG Reporter application."""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Import and run the application
if __name__ in {"__main__", "__mp_main__"}:  
    from app.ui.main_app import create_app
    create_app()
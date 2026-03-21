"""Common path constants for pipeline scripts."""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add project root to sys.path so pipeline scripts can import models.py
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

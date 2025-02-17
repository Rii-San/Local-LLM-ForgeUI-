import os
import sys

# Get the absolute path of the modules directory
MODULES_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure the parent directory is in sys.path so ui.py can find modules
PARENT_DIR = os.path.abspath(os.path.join(MODULES_DIR, os.pardir))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import necessary modules
from .forgeUI import *
from .llm import *

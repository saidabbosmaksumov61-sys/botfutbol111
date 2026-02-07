import sys
import os

# Set path to current directory
sys.path.append(os.getcwd())

try:
    import locales
    print(f"Locales found at: {locales.__file__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

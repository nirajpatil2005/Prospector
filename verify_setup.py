import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("Successfully imported app.main")
except ImportError as e:
    print(f"Failed to import app.main: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error during import: {e}")
    sys.exit(1)

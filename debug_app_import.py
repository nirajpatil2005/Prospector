import sys
import os
import app.main
print(f"App Main File: {app.main.__file__}")
print(f"App object: {app.main.app}")
print(f"Routes: {[r.path for r in app.main.app.routes]}")

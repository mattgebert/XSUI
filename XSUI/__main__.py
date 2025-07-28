"""
Define the main entry point for the XSUI web application.
"""

# Prevent use of pycache.
import sys

sys.dont_write_bytecode = True

import subprocess, os

# # Attempt to run the XSUI webapp application
# path = os.getcwd()
# app_path = os.path.join(path, "XSUI", "webapp", "fastapi", "main.py")
# print(f"Launching XSUI webapp at {app_path}...")
# subprocess.run(["fastapi", "dev", app_path], shell=True, check=True)

path = os.getcwd()

# Pure Dash App:
# app_path = os.path.join(path, "XSUI", "webapp", "dash", "main.py")

# FastAPI App:
app_path = os.path.join(path, "XSUI", "webapp", "fastapi", "main.py")

print(f"Launching XSUI webapp at {app_path}...")
subprocess.run(["python", app_path], shell=True, check=True)

"""
Define the main entry point for the XSUI web application.
"""

import os
import subprocess
import sys

# Prevent use of pycache.
sys.dont_write_bytecode = True

# # Attempt to run the XSUI webapp application
# path = os.getcwd()
# app_path = os.path.join(path, "XSUI", "webapp", "fastapi", "main.py")
# print(f"Launching XSUI webapp at {app_path}...")
# subprocess.run(["fastapi", "dev", app_path], shell=True, check=True)

def main() -> None:
	"""Launch the XSUI FastAPI application via the current Python interpreter."""
	path = os.getcwd()
	"""Current working directory used to construct the app path."""

	app_path = os.path.join(path, "XSUI", "webapp", "fastapi", "main.py")
	"""Path to the FastAPI entry module."""

	print(f"Launching XSUI webapp at {app_path}...")
	subprocess.run([sys.executable, app_path], shell=False, check=True)


if __name__ == "__main__":
	main()

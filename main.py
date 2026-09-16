#!/usr/bin/env python3
"""Network Engineer Simulator 3D - Main Application Entry Point."""

import os
import sys
import subprocess


def bootstrap_runtime() -> None:
    """Ensure runtime compatibility with pre-installed pygame & PyOpenGL."""
    try:
        import pygame
        import OpenGL
    except ImportError:
        # Check if Windows py launcher can run Python 3.11 which has the required modules installed
        if sys.platform.startswith("win"):
            print("[Bootstrap] pygame or PyOpenGL not found in current environment.")
            print("[Bootstrap] Detecting Python 3.11 runtime...")
            try:
                result = subprocess.run(["py", "-3.11", "-c", "import pygame, OpenGL; print('OK')"], capture_output=True, text=True)
                if "OK" in result.stdout:
                    print("[Bootstrap] Python 3.11 runtime found. Relaunching main.py under Python 3.11...")
                    sys.exit(subprocess.call(["py", "-3.11", __file__] + sys.argv[1:]))
            except Exception as e:
                print(f"[Bootstrap Warning] Could not auto-relaunch with py -3.11: {e}")

        print("Error: Missing required packages. Please install requirements with:")
        print("    pip install -r requirements.txt")
        print("or run with Python 3.11:")
        print("    py -3.11 main.py")
        sys.exit(1)


def main() -> None:
    """Initialize and run the simulator."""
    bootstrap_runtime()

    # Ensure working directory is the script folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from core.game import Game

    print("==================================================")
    print("      NETWORK ENGINEER SIMULATOR 3D (v1.0)        ")
    print("==================================================")
    print("Starting simulation engine...")

    game = Game()
    game.run()


if __name__ == "__main__":
    main()

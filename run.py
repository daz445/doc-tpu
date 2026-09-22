"""Standalone entry point for PyInstaller build."""
import sys
import os

# Ensure doc_tpu package is importable
sys.path.insert(0, os.path.dirname(__file__))

from doc_tpu.cli import main

if __name__ == "__main__":
    main()

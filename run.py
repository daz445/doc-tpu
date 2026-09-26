"""Entry point для PyInstaller standalone binary."""

import sys
import os

# Добавляем корень проекта в путь для импорта
if getattr(sys, 'frozen', False):
    # PyInstaller bundle
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_dir)

from doc_tpu.cli import main

if __name__ == "__main__":
    main()

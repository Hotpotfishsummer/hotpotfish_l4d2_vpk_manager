"""
L4D2 VPK Manager Entry Point
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app import main
import flet as ft


if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error running app: {e}", file=sys.stderr)
        sys.exit(1)

"""打包入口（供 PyInstaller 使用，位于包外以规避相对导入）。"""
import sys

from src.main import main

if __name__ == "__main__":
    sys.exit(main())

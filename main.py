"""
L4D2 VPK Manager Entry Point
"""
import sys
from pathlib import Path
import io
import zstandard  # 强制打包工具识别此依赖

# Create log file for debugging
log_file = Path(__file__).parent / "app_debug.log"
log_handle = open(log_file, "w", encoding="utf-8")

def debug_log(msg: str):
    """Write debug message to both console and log file"""
    try:
        print(msg)
        log_handle.write(msg + "\n")
        log_handle.flush()
    except Exception as e:
        try:
            log_handle.write(f"Logging error: {e}\n")
            log_handle.flush()
        except:
            pass

debug_log(f"Application started from: {__file__}")
debug_log(f"Working directory: {Path.cwd()}")
debug_log(f"Python path: {sys.path}")

# Import flet FIRST before modifying sys.path
try:
    import flet as ft
    debug_log("✓ Flet imported successfully")
except Exception as e:
    debug_log(f"✗ Failed to import Flet: {e}")
    sys.exit(1)

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent / "src"
debug_log(f"Adding to sys.path: {src_path}")
debug_log(f"src path exists: {src_path.exists()}")
sys.path.insert(0, str(src_path))

# Set UTF-8 encoding for stdout and stderr to handle special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Now import the app main function
try:
    from app import main
    debug_log("✓ App main function imported successfully")
except Exception as e:
    debug_log(f"✗ Failed to import app.main: {e}")
    import traceback
    debug_log(traceback.format_exc())
    sys.exit(1)


if __name__ == "__main__":
    try:
        debug_log("Starting Flet application...")
        ft.app(target=main)
        debug_log("Flet app closed normally")
    except Exception as e:
        debug_log(f"✗ Error running app: {e}")
        import traceback
        debug_log(traceback.format_exc())
        sys.exit(1)
    finally:
        log_handle.close()

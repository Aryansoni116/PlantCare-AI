"""
PlantDiseaseAI - One-Click Launcher
=====================================
Run this file to start the backend server AND open the app in your browser automatically.

Usage:
    python start.py
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

# Fix Windows terminal encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Config ----------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8080
APP_URL = f"http://{HOST}:{PORT}"
BANNER = """
+----------------------------------------------------------+
|        PlantDiseaseAI  --  Starting Up...               |
+----------------------------------------------------------+
"""

# ── Helpers ─────────────────────────────────────────────────
def is_port_open(host: str, port: int) -> bool:
    """Check if the server is accepting connections yet."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_server(host: str, port: int, timeout: int = 120) -> bool:
    """Poll until the server is ready or timeout is reached."""
    print(f"⏳ Waiting for server at {APP_URL} ...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(host, port):
            print(" Ready! ✅")
            return True
        print(".", end="", flush=True)
        time.sleep(0.5)
    print(" Timed out ❌")
    return False


def check_env():
    """Warn if .env file or Gemini key is missing."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("⚠️  WARNING: .env file not found. Create one from .env.example")
    else:
        content = env_path.read_text()
        if "your_grok_api_key_here" in content or "GROK_API_KEY=" not in content:
            print("⚠️  WARNING: GROK_API_KEY is not set in .env — explanation features will use mock data.")


# ── Main ─────────────────────────────────────────────────────
def main():
    print(BANNER)

    # Move to project root so relative paths in app.py work correctly
    os.chdir(Path(__file__).parent)

    # Check environment
    check_env()

    print(f"🚀 Starting FastAPI backend on {APP_URL}")
    print("   Press  Ctrl + C  to stop the server.\n")

    # Start uvicorn as a subprocess
    server_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", HOST,
            "--port", str(PORT),
            "--reload",           # Auto-reload on code changes
        ],
        cwd=Path(__file__).parent
    )

    try:
        # Wait until the server is ready, then open the browser
        if wait_for_server(HOST, PORT, timeout=30):
            print(f"🌐 Opening browser → {APP_URL}\n")
            webbrowser.open(APP_URL)
        else:
            print("❌ Server did not start in time. Check for errors above.")

        # Keep running until Ctrl+C
        server_process.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down PlantDiseaseAI server... Goodbye!")
        server_process.terminate()
        server_process.wait()
        sys.exit(0)


if __name__ == "__main__":
    main()

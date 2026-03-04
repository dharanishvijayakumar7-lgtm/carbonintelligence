#!/usr/bin/env python3
"""
🌍 Carbon Intelligence — Easy Startup Script
Run this single file to start everything!

Usage:
    python start.py          # Start API only
    python start.py --all    # Start API + Dashboard
    python start.py --stop   # Stop all servers
"""
import subprocess
import sys
import time
import os
import signal

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python")

def check_port(port):
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port(port):
    """Kill process on a port."""
    try:
        result = subprocess.run(
            f"lsof -ti:{port} | xargs kill -9 2>/dev/null",
            shell=True, capture_output=True
        )
        return True
    except:
        return False

def start_api():
    """Start the FastAPI/Flask backend."""
    print("🚀 Starting API server on http://127.0.0.1:8000")
    
    # Check if main.py or app.py exists
    if os.path.exists(os.path.join(BASE_DIR, "app.py")):
        api_file = "app.py"
    else:
        api_file = "main.py"
    
    # Use uvicorn for FastAPI, or direct python for Flask
    if api_file == "main.py":
        cmd = [VENV_PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
    else:
        cmd = [VENV_PYTHON, api_file]
    
    return subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def start_dashboard():
    """Start the Streamlit dashboard."""
    print("📊 Starting Dashboard on http://127.0.0.1:8501")
    
    return subprocess.Popen(
        [VENV_PYTHON, "-m", "streamlit", "run", "dashboard.py", 
         "--server.port", "8501", "--server.headless", "true"],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def wait_for_api(timeout=30):
    """Wait for API to be ready."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)
            return True
        except:
            time.sleep(0.5)
    return False

def main():
    print()
    print("=" * 50)
    print("🌍 CARBON INTELLIGENCE SYSTEM")
    print("=" * 50)
    print()
    
    # Handle --stop flag
    if "--stop" in sys.argv:
        print("🛑 Stopping all servers...")
        kill_port(8000)
        kill_port(8501)
        print("✅ All servers stopped")
        return
    
    # Check if ports are in use
    if check_port(8000):
        print("⚠️  Port 8000 already in use. Killing existing process...")
        kill_port(8000)
        time.sleep(1)
    
    if "--all" in sys.argv and check_port(8501):
        print("⚠️  Port 8501 already in use. Killing existing process...")
        kill_port(8501)
        time.sleep(1)
    
    # Start API
    api_proc = start_api()
    
    # Wait for API to be ready
    print("⏳ Waiting for API to start...")
    if wait_for_api():
        print("✅ API is ready!")
    else:
        print("❌ API failed to start. Check the logs.")
        api_proc.terminate()
        return
    
    # Start dashboard if --all flag
    dashboard_proc = None
    if "--all" in sys.argv:
        dashboard_proc = start_dashboard()
        time.sleep(3)
        print("✅ Dashboard is ready!")
    
    print()
    print("=" * 50)
    print("🎉 SYSTEM READY!")
    print("=" * 50)
    print()
    print("📡 API:        http://127.0.0.1:8000")
    print("📖 API Docs:   http://127.0.0.1:8000/docs")
    if "--all" in sys.argv:
        print("📊 Dashboard:  http://127.0.0.1:8501")
    else:
        print()
        print("💡 To start dashboard, run in another terminal:")
        print("   streamlit run dashboard.py")
    print()
    print("Press Ctrl+C to stop all servers")
    print()
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down...")
        api_proc.terminate()
        if dashboard_proc:
            dashboard_proc.terminate()
        print("✅ Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep running and show logs
    try:
        while True:
            # Read API output
            line = api_proc.stdout.readline()
            if line:
                print(line.decode().strip())
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

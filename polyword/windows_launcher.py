import os
import sys
import webbrowser
import threading
import uvicorn
from pathlib import Path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        "polyword.api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

def main():
    # Set up credentials path
    credentials_path = resource_path('gcpkey.json')
    if not os.path.exists(credentials_path):
        print(f"Error: Could not find credentials file at {credentials_path}")
        print("Please ensure gcpkey.json is in the same directory as the executable")
        input("Press Enter to exit...")
        sys.exit(1)
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Wait for server to start
    import time
    time.sleep(2)

    # Open browser
    webbrowser.open('http://127.0.0.1:8000/')

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Simple startup script for the Life Expectancy Lookup web tool.
This will automatically open your browser to the tool.
"""

import webbrowser
import time
import subprocess
import sys
import os
import socket

def find_free_port():
    """Find a free port to use."""
    for port in range(5000, 5020):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return 8080  # fallback port

def check_flask():
    """Check if Flask is installed."""
    try:
        import flask
        return True
    except ImportError:
        return False

def install_flask():
    """Install Flask if not available."""
    print("Flask not found. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("Starting Life Expectancy Lookup Web Tool...")
    
    # Check if Flask is available
    if not check_flask():
        if not install_flask():
            print("Failed to install Flask. Please install it manually:")
            print("pip install flask")
            return
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("Loading data files...")
    
    # Find an available port
    port = find_free_port()
    url = f'http://localhost:{port}'
    
    # Start the Flask app in a subprocess
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(url)
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start Flask app
        from app import app, init_lookup
        if init_lookup():
            print("Data loaded successfully!")
            print(f"Opening web browser at {url}")
            print("Press Ctrl+C to stop the server")
            app.run(debug=False, host='127.0.0.1', port=port)
        else:
            print("Failed to load data files. Check file paths in expectancy_lookup.py")
            
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
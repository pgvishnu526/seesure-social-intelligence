#!/usr/bin/env python3
"""
Simple frontend server for SocialPulse
"""

import os
import sys
import http.server
import socketserver
import webbrowser
from pathlib import Path

def start_frontend_server(port=8080):
    """Start a simple HTTP server for the frontend"""
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("Error: frontend directory not found")
        sys.exit(1)
    
    os.chdir(frontend_dir)
    
    # Create a custom handler to serve files
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"SocialPulse Frontend Server")
            print(f"Serving at: http://localhost:{port}")
            print(f"Make sure backend is running at: http://localhost:8000")
            print("\nPress Ctrl+C to stop the server\n")
            
            # Try to open browser
            try:
                webbrowser.open(f"http://localhost:{port}")
            except:
                pass
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\nFrontend server stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {port} is already in use")
            print(f"Try a different port: python start_frontend.py --port 8081")
        else:
            print(f"Error starting server: {e}")

def main():
    """Main frontend server startup"""
    port = 8080
    
    # Check for custom port
    if len(sys.argv) > 1:
        if sys.argv[1] == "--port" and len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print("Invalid port number")
                sys.exit(1)
    
    start_frontend_server(port)

if __name__ == "__main__":
    main()
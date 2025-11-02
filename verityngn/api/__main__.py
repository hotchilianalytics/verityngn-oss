"""
Entry point for running the VerityNgn API server.

Usage:
    python -m verityngn.api
    python -m verityngn.api --host 0.0.0.0 --port 8000
"""

import uvicorn
import sys
from verityngn.api import app

if __name__ == "__main__":
    import socket
    
    # Parse command line arguments
    host = "0.0.0.0"
    port = 8000
    
    # Check for --host and --port arguments
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]
    
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    
    # Check if port is available, try alternative ports if not
    def find_available_port(start_port: int, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port."""
        for attempt in range(max_attempts):
            test_port = start_port + attempt
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('0.0.0.0', test_port))
                sock.close()
                return test_port
            except OSError:
                sock.close()
                continue
        raise RuntimeError(f"Could not find available port starting from {start_port}")
    
    # If port is specified, try it first; if busy, find alternative
    if port == 8000 and "--port" not in sys.argv:
        # Only auto-find if default port and not explicitly set
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
        except OSError:
            print(f"⚠️  Port {port} is already in use. Finding alternative port...")
            port = find_available_port(8001)
            print(f"✅ Using port {port} instead")
    
    print(f"🚀 Starting VerityNgn API server on http://{host}:{port}")
    print(f"📊 API docs available at http://{host}:{port}/docs")
    print(f"📄 Reports available at http://{host}:{port}/api/v1/reports/{{video_id}}/report.html")
    
    uvicorn.run(app, host=host, port=port)


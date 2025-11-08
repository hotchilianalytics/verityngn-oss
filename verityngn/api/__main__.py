"""
Entry point for running the VerityNgn API server.

Usage:
    python -m verityngn.api
    python -m verityngn.api --host 0.0.0.0 --port 8080
    PORT=8080 python -m verityngn.api
"""

import uvicorn
import sys
import os
from verityngn.api import app

if __name__ == "__main__":
    import socket
    
    # Parse command line arguments and environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))  # Default to 8080 to match Docker config
    
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
    if port == 8080 and "--port" not in sys.argv and "PORT" not in os.environ:
        # Only auto-find if default port and not explicitly set via CLI or ENV
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
        except OSError:
            print(f"⚠️  Port {port} is already in use. Finding alternative port...")
            port = find_available_port(8081)
            print(f"✅ Using port {port} instead")
    
    print(f"🚀 Starting VerityNgn API server on http://{host}:{port}")
    print(f"📊 API docs available at http://{host}:{port}/docs")
    print(f"📄 Reports available at http://{host}:{port}/api/v1/reports/{{video_id}}/report.html")
    
    # Configure logging to reduce noise from status polling and health checks
    import logging
    
    # Create custom log config that silences uvicorn access logs
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(levelname)s: %(message)s",
            },
            "access": {
                "format": '%(levelname)s: %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "WARNING"},  # Silence access logs
        },
    }
    
    uvicorn.run(app, host=host, port=port, log_config=log_config)


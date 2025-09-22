#!/usr/bin/env python3
"""
Boussinesq Stress Analysis - Production Runner
Provides options for running in development or production mode
"""

import os
import sys
import argparse
from app import app

def main():
    parser = argparse.ArgumentParser(description='Boussinesq Stress Analysis Web Application')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8050, help='Port to bind to (default: 8050)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--production', action='store_true', help='Run in production mode with gunicorn')
    parser.add_argument('--workers', type=int, default=4, help='Number of gunicorn workers (production mode)')
    
    args = parser.parse_args()
    
    if args.production:
        # Production mode with gunicorn
        print("🚀 Starting in production mode with gunicorn...")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Workers: {args.workers}")
        
        # Check if gunicorn is available
        try:
            import gunicorn
        except ImportError:
            print("❌ gunicorn not found. Install it with: pip install gunicorn")
            sys.exit(1)
        
        # Run with gunicorn
        os.system(f"gunicorn --bind {args.host}:{args.port} --workers {args.workers} app:app.server")
    else:
        # Development mode
        print("🛠️  Starting in development mode...")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Debug: {args.debug}")
        print(f"   Open: http://{args.host}:{args.port}")
        
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            dev_tools_hot_reload=args.debug,
            dev_tools_ui=args.debug
        )

if __name__ == '__main__':
    main()

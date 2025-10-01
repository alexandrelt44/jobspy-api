#!/usr/bin/env python3
"""
Script to run the JobSpy API server
"""

import uvicorn
import sys
import argparse


def main():
    """Main function to start the API server"""
    parser = argparse.ArgumentParser(description="Run JobSpy API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    print("🚀 Starting JobSpy API server...")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📖 API documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Alternative docs: http://{args.host}:{args.port}/redoc")
    
    if args.reload:
        print("🔄 Auto-reload enabled (development mode)")
    
    print("\n" + "="*60)
    
    try:
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,  # reload doesn't work with multiple workers
            log_level="info",
            timeout_keep_alive=300,  # 5 minutes for keep-alive connections
            timeout_graceful_shutdown=30  # 30 seconds for graceful shutdown
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
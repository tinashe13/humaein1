#!/usr/bin/env python3
"""
Development server runner for Windows with proper logging setup.
Fixes reload hanging issues with dictConfig and WatchFiles conflicts.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import structlog
import uvicorn


def setup_dev_logging() -> None:
    """Configure logging for development with idempotent setup."""
    # Clear any existing handlers to avoid conflicts on reload
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Clear structlog configuration
    structlog.reset_defaults()
    
    # Simple console logging for development
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override existing configuration
    )
    
    # Configure structlog for development
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def create_dev_app():
    """Create FastAPI app with development-specific settings."""
    # Set up logging first, before importing the app
    setup_dev_logging()
    
    # Import here to avoid circular import and ensure logging is set up
    from .main import create_app
    
    app = create_app()
    
    # Add development-specific middleware or settings here if needed
    return app


def main() -> None:
    """Run the development server."""
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Development server configuration
    host = os.getenv("DEV_HOST", "127.0.0.1")
    port = int(os.getenv("DEV_PORT", "8000"))
    reload = os.getenv("DEV_RELOAD", "1").lower() in ("1", "true", "yes")
    
    print(f"🚀 Starting development server on http://{host}:{port}")
    print(f"📁 Working directory: {backend_dir}")
    print(f"🔄 Hot reload: {'enabled' if reload else 'disabled'}")
    
    # Custom uvicorn configuration for development
    uvicorn.run(
        "app.devserver:create_dev_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(backend_dir / "app")],
        log_config=None,  # Disable uvicorn's logging config to prevent conflicts
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    main()

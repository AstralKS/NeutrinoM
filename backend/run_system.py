import logging
import subprocess
import sys
import time
import signal
import os
import threading
from pathlib import Path

# Configure Logging
LOG_FILE = "advisor.log"

def setup_logging():
    """Configure logging to both console and file."""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatters
    # Console gets color/simple format, File gets detailed timestamp
    console_formatter = logging.Formatter('%(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    
    # Send a starup message
    logging.info(f"Logging configured. Writing to {LOG_FILE}")

def log_stream(process_name, stream, logger):
    """Read stream line by line and log it."""
    for line in iter(stream.readline, b''):
        line_str = line.decode('utf-8', errors='replace').strip()
        if line_str:
            logger.info(f"[{process_name}] {line_str}")
    stream.close()

def run_backend():
    """Start the FastAPI backend server."""
    logging.info("Starting Backend Server...")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "advisor.api.endpoints:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(Path(__file__).parent / "src"),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT 
    )

def run_frontend():
    """Start the Streamlit frontend."""
    logging.info("Starting Frontend Server...")
    app_path = Path(__file__).parent / "src" / "advisor" / "ui" / "app.py"
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        cwd=str(Path(__file__).parent),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

def main():
    setup_logging()
    logger = logging.getLogger("SystemRunner")
    
    backend_process = None
    frontend_process = None

    try:
        logger.info("Initializing System...")
        
        # Start Backend
        backend_process = run_backend()
        # Start thread to capture logs
        t_backend = threading.Thread(target=log_stream, args=("BACKEND", backend_process.stdout, logger))
        t_backend.daemon = True
        t_backend.start()
        
        time.sleep(2) 
        
        if backend_process.poll() is not None:
             logger.error("Backend failed to start.")
             return

        # Start Frontend
        frontend_process = run_frontend()
        # Start thread to capture logs
        t_frontend = threading.Thread(target=log_stream, args=("FRONTEND", frontend_process.stdout, logger))
        t_frontend.daemon = True
        t_frontend.start()
        
        logger.info("System Running. Press Ctrl+C to stop.")
        
        # Keep main process alive
        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                 logger.error(f"Backend process ended unexpectedly with code {backend_process.returncode}")
                 break
            if frontend_process.poll() is not None:
                 logger.error(f"Frontend process ended unexpectedly with code {frontend_process.returncode}")
                 break

    except KeyboardInterrupt:
        logger.info("\nStopping system...")
    finally:
        logger.info("Terminating processes...")
        if frontend_process:
            frontend_process.terminate()
        if backend_process:
            backend_process.terminate()
        
        # Give them a moment to die
        time.sleep(1)
        
        if frontend_process and frontend_process.poll() is None:
             frontend_process.kill()
        if backend_process and backend_process.poll() is None:
             backend_process.kill()
             
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    main()

import psutil
import time
import datetime
import logging
import os # Added to ensure the log directory exists

# --- Configuration ---
LOG_FILE = "system_performance.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
SAMPLING_INTERVAL_SECONDS = 5  # Time between each data log in seconds
MAX_LOG_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Number of backup log files to keep

# --- Setup Logging ---
def setup_logger(log_file, log_level, log_format, max_bytes, backup_count):
    """Configures and returns a logger instance."""
    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("SystemMonitor")
    logger.setLevel(log_level)

    # Use RotatingFileHandler for log rotation
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8' # Added encoding for wider compatibility
    )
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Optional: Add a console handler to also print logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# --- Main Monitoring Function ---
def monitor_system(logger, interval_seconds):
    """Monitors CPU and memory usage and logs the data."""
    logger.info("Starting system performance monitoring.")
    print(f"Logging data every {interval_seconds} seconds to {LOG_FILE}. Press Ctrl+C to stop.")
    try:
        while True:
            # Get current timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get CPU usage
            # interval=1 means it will block for 1 second to compare CPU times
            # Set to a small value or None for non-blocking, but potentially less accurate initial readings.
            # For continuous monitoring, subsequent calls to cpu_percent(interval=None) after an initial call
            # with an interval will give the percentage since the last call.
            # Here, we use the specified interval for each reading for simplicity.
            cpu_usage = psutil.cpu_percent(interval=1) # Ensure this interval is less than SAMPLING_INTERVAL_SECONDS if precise timing is critical

            # Get Memory usage
            memory_info = psutil.virtual_memory()
            memory_usage_percent = memory_info.percent
            memory_used_mb = memory_info.used / (1024 * 1024) # Convert bytes to MB
            memory_total_mb = memory_info.total / (1024 * 1024) # Convert bytes to MB

            # Log the data
            log_message = (
                f"CPU Usage: {cpu_usage:.2f}%, "
                f"Memory Usage: {memory_usage_percent:.2f}% "
                f"({memory_used_mb:.2f}MB / {memory_total_mb:.2f}MB)"
            )
            logger.info(log_message)

            # Wait for the next sampling interval
            # Adjust sleep time if psutil.cpu_percent interval is significant
            sleep_time = interval_seconds - 1 # Subtracting the cpu_percent interval
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif interval_seconds < 1 : # Handle cases where sampling interval is very short
                 time.sleep(interval_seconds)


    except KeyboardInterrupt:
        logger.info("System performance monitoring stopped by user.")
        print("\nMonitoring stopped.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ensure psutil is installed
    try:
        import psutil
    except ImportError:
        print("Error: The 'psutil' library is not installed.")
        print("Please install it by running: pip install psutil")
        exit(1)

    # Ensure logging.handlers is available (standard library)
    try:
        import logging.handlers
    except ImportError:
        print("Error: logging.handlers module not found. This is unexpected for standard Python installs.")
        exit(1)


    performance_logger = setup_logger(
        LOG_FILE,
        LOG_LEVEL,
        LOG_FORMAT,
        MAX_LOG_FILE_SIZE_BYTES,
        BACKUP_COUNT
    )
    monitor_system(performance_logger, SAMPLING_INTERVAL_SECONDS)
import psutil
import time
import datetime
import logging
import logging.handlers # Yeah, need this for the rotating logs
import os
import sys # For messing with the terminal output

# --- Stuff you might want to change ---
LOG_FILE = "system_performance_stats.log" # Where we're saving the detailed stats
LOG_FORMAT = "%(asctime)s - %(message)s" # Keeping the log format simple: time and the message
LOG_LEVEL = logging.INFO # INFO level should be good for normal stats
SAMPLING_INTERVAL_SECONDS = 1  # How often we grab data, 1 second feels pretty live
MAX_LOG_FILE_SIZE_BYTES = 5 * 1024 * 1024  # Let's keep log files to around 5MB before they roll over
BACKUP_COUNT = 3  # And keep 3 old ones

# For the cool terminal bars
BAR_WIDTH = 35  # How wide the bars look on the screen
FILLED_CHAR = '❚' # Using a slightly different char for fun
EMPTY_CHAR = '·' # Light dot for empty part

# --- Setting up our log file ---
def setup_file_logger(log_file, log_level, log_format, max_bytes, backup_count):
    # "Sets up a logger that writes to a file and rotates it when it gets too big."
    # Make sure the folder for the log file actually exists
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if log_dir and not os.path.exists(log_dir):
        print(f"Log directory {log_dir} doesn't exist, creating it.")
        os.makedirs(log_dir)

    # Get a logger instance, let's name it so it's clear what it's for
    my_logger = logging.getLogger("PerformanceFileLogger")
    my_logger.setLevel(log_level)
    # Stop messages from bubbling up to the root logger, if that's doing something else
    my_logger.propagate = False

    # This is the handler that writes to our file and handles rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8' # Good for handling various characters
    )
    # How each log line should look
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    my_logger.addHandler(file_handler)

    return my_logger

# --- Helper for making those progress bars ---
def make_that_bar(percentage, width, filled_char, empty_char):
    # "Turns a percentage into a text-based progress bar string. Looks neat!"
    # Just in case the percentage is wild, clamp it between 0 and 100
    percentage = max(0, min(100, float(percentage)))
    filled_part_length = int(width * percentage / 100)
    # Build the bar: some filled chars, then some empty ones
    bar_itself = filled_char * filled_part_length + empty_char * (width - filled_part_length)
    return f"[{bar_itself}] {percentage:.1f}%" # Show percentage with one decimal

# --- The main show: monitoring and logging! ---
def watch_and_log(file_logger_instance, update_interval_secs):
    # "This is where the magic happens: grabs stats, logs 'em, shows 'em."
    print(f"Alright, starting up! I'll log stats every {update_interval_secs} sec to '{LOG_FILE}'.")
    print("You'll see live bars below. Press Ctrl+C to stop me.")
    file_logger_instance.info("Monitoring started.") # Log that we've started

    # psutil.cpu_percent needs an initial call with an interval to start measuring correctly.
    # After that, interval=None gives usage since the last call.
    psutil.cpu_percent(interval=0.1)
    time.sleep(0.1) # Just a tiny pause

    try:
        while True:
            # Grab CPU usage - non-blocking after the initial setup call
            current_cpu_usage = psutil.cpu_percent(interval=None)

            # Get RAM details
            memory_stats = psutil.virtual_memory()
            current_memory_percent = memory_stats.percent
            # Let's show used/total memory in MB, it's more human-readable
            memory_used_mb = memory_stats.used / (1024 * 1024)
            memory_total_mb = memory_stats.total / (1024 * 1024)

            # What we're writing to the log file
            # Making it a bit more like a status update
            log_entry = (
                f"Tick - CPU: {current_cpu_usage:.1f}%, "
                f"RAM: {current_memory_percent:.1f}% "
                f"({memory_used_mb:.1f}/{memory_total_mb:.1f} MB)"
            )
            file_logger_instance.info(log_entry)

            # --- Time for the terminal graphics! ---
            cpu_bar_str = make_that_bar(current_cpu_usage, BAR_WIDTH, FILLED_CHAR, EMPTY_CHAR)
            mem_bar_str = make_that_bar(current_memory_percent, BAR_WIDTH, FILLED_CHAR, EMPTY_CHAR)

            # Try to get the terminal width so the line clears properly
            try:
                term_width = os.get_terminal_size().columns
            except OSError: # If it's not a real terminal (e.g., output piped to a file)
                term_width = 80 # Just guess a standard width

            # The string that'll show up on the terminal
            # Adding a small space at the end of "CPU" for alignment
            terminal_display_string = f"CPU : {cpu_bar_str}   RAM : {mem_bar_str}"
            # Some padding to wipe the previous line's content if it was longer
            padding_spaces = " " * (term_width - len(terminal_display_string) - 1)

            # \r moves the cursor to the start of the line
            sys.stdout.write(f"\r{terminal_display_string}{padding_spaces}")
            sys.stdout.flush() # Make sure it shows up right away

            # Chill for a bit before the next update
            time.sleep(update_interval_secs)

    except KeyboardInterrupt:
        # User hit Ctrl+C, let's clean up the terminal line
        sys.stdout.write("\n")
        print("Okay, okay, I'm stopping! Log file has the history.")
        file_logger_instance.info("Monitoring stopped by user.")
    except Exception as e:
        # Whoops, something went wrong
        sys.stdout.write("\n")
        print(f"\nOh no, an error popped up: {e}")
        file_logger_instance.error(f"Bummer, an error happened: {e}", exc_info=True) # Log the full error
    finally:
        # Just to be sure the cursor is on a new line when we exit
        sys.stdout.write("\n")


if __name__ == "__main__":
    # Quick check: does the user even have psutil?
    try:
        import psutil
    except ImportError:
        print("Hold up! You need the 'psutil' library for this script to work.")
        print("Try running: pip install psutil")
        sys.exit(1) # Can't do much without it

    # Get our logger ready for action
    my_awesome_file_logger = setup_file_logger(
        LOG_FILE,
        LOG_LEVEL,
        LOG_FORMAT,
        MAX_LOG_FILE_SIZE_BYTES,
        BACKUP_COUNT
    )
    # And... go!
    watch_and_log(my_awesome_file_logger, SAMPLING_INTERVAL_SECONDS)
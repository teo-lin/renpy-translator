"""
Utility functions for poly_trans.
"""

import time


def show_progress(current, total, start_time, prefix=""):
    """Display simple progress bar with >>> characters and time labels"""
    percentage = (current / total) * 100 if total > 0 else 0
    elapsed = time.time() - start_time

    # Calculate ETA
    if current > 0 and elapsed > 0:
        rate = current / elapsed
        remaining = (total - current) / rate if rate > 0 else 0
    else:
        remaining = 0

    # Format time strings
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{int(elapsed)}s"
    remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s" if remaining >= 60 else f"{int(remaining)}s"

    # Create progress bar with >>> characters
    bar_width = 50
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = ">" * filled + " " * (bar_width - filled)

    # Display with labels
    print(f"\r{prefix}[{bar}] {current}/{total} ({percentage:.0f}%) | Elapsed: {elapsed_str} | ETA: {remaining_str}",
          end='', flush=True)

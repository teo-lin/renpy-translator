"""
Utility functions for poly_trans.
"""

import time


_PROGRESS_DOTS_PER_LINE = 50


def show_progress(current, total, start_time, prefix=""):
    """Append one dot per tick; emit a status line every 50 ticks (and at the end).
    Avoids \\r-style overwriting since some terminals/pipes treat it as a newline."""
    if total <= 0:
        return
    if (current - 1) % _PROGRESS_DOTS_PER_LINE == 0:
        print(prefix, end="", flush=True)
    print(".", end="", flush=True)
    if current % _PROGRESS_DOTS_PER_LINE == 0 or current == total:
        elapsed = time.time() - start_time
        rate = current / elapsed if (current > 0 and elapsed > 0) else 0
        remaining = (total - current) / rate if rate > 0 else 0
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{int(elapsed)}s"
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s" if remaining >= 60 else f"{int(remaining)}s"
        percentage = (current / total) * 100
        print(f" {current}/{total} ({percentage:.0f}%) | {elapsed_str} elapsed | ETA {remaining_str}",
              flush=True)

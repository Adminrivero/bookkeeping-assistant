import logging

use_logging = False  # global flag, toggled by CLI

def notify(message: str, level: str = "info"):
    """
    Unified output helper.
    - By default, prints to stdout.
    - If logging is enabled, uses Python's logging module.
    """
    if use_logging:
        log_fn = getattr(logging, level, logging.info)
        log_fn(message)
    else:
        print(message)

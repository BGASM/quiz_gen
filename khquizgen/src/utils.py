import functools
import sys
from loguru import logger


# Set up logging filter. Later check if DEBUG_PATH set, if it is, we switch back to debug
def my_filter(record):
    if record["extra"].get("debug_off"):  # "warn_only" is bound to the logger and set to 'True'
        return record["level"].no >= logger.level("INFO").no
    return True  # Fallback to default 'level' configured while adding the handler


# Initial setup for loggers.
logger.remove(0)
logger.add(sys.stderr, filter=my_filter, level="DEBUG")
logger = logger.bind(debug_off=True)
logger_b = logger.bind(name="b")


def logger_wraps(*, entry=True, exit=True, level="TRACE"):
    def wrapper(func):
        name = func.__name__
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger_b.opt(depth=1)
            if entry:
                logger_.log(level, "Entering '{}' (kwargs={})", name, kwargs)
            result = func(*args, **kwargs)
            if exit:
                logger_.log(level, "Exiting '{}' (result={})", name, result)
            return result
        return wrapped
    return wrapper

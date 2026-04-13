import time
import logging
import functools

def timer(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        """Times the execution of the decorated function."""
        # Time the function duration
        start = time.time()
        res = method(self, *args, **kwargs)
        end = time.time()
        dur = end - start

        # Get a logger instance (stacklevel=2 uses the logger from the function being decorated)
        logger = logging.getLogger(self.__class__.__module__)
        logger.info(f"{method.__name__}: {dur:.4f} s", stacklevel=2)

        return res
    return wrapper

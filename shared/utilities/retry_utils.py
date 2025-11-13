"""
Retry utilities for handling transient failures with exponential backoff.

This module provides decorators and functions for implementing automatic retry
logic with exponential backoff for operations that may fail transiently.
"""

import time
import logging
from typing import Callable, Type, Tuple, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def exponential_backoff(attempt: int, backoff_factor: float = 2.0, base_delay: float = 1.0) -> float:
    """
    Calculate delay for exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        backoff_factor: Multiplier for each retry (default: 2.0)
        base_delay: Base delay in seconds (default: 1.0)

    Returns:
        Delay in seconds for this attempt

    Example:
        attempt=0 → 1s
        attempt=1 → 2s
        attempt=2 → 4s
    """
    return base_delay * (backoff_factor ** attempt)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    base_delay: float = 1.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (ValueError, TypeError, KeyError)
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_factor: Multiplier for each retry (default: 2.0)
        base_delay: Base delay in seconds (default: 1.0)
        retryable_exceptions: Tuple of exception types to retry
        non_retryable_exceptions: Tuple of exception types to fail immediately

    Usage:
        @retry(max_attempts=3, backoff_factor=2, base_delay=1)
        def flaky_operation():
            # Operation that may fail transiently
            pass

    Example:
        Attempt 1 fails → wait 1s → Attempt 2 fails → wait 2s → Attempt 3 succeeds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)

                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_attempts}"
                        )

                    return result

                except non_retryable_exceptions as e:
                    # Validation errors - fail immediately, no retry
                    logger.error(
                        f"{func.__name__} failed with non-retryable error: {e}"
                    )
                    raise

                except retryable_exceptions as e:
                    last_exception = e

                    # Last attempt - don't wait, just raise
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        break

                    # Calculate delay and wait
                    delay = exponential_backoff(attempt, backoff_factor, base_delay)
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            # All attempts exhausted
            raise RetryError(
                f"{func.__name__} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception

        return wrapper
    return decorator


def retry_async(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    base_delay: float = 1.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (ValueError, TypeError, KeyError)
):
    """
    Decorator for automatic retry with exponential backoff (async version).

    Same as retry() but for async functions.

    Usage:
        @retry_async(max_attempts=3, backoff_factor=2, base_delay=1)
        async def flaky_async_operation():
            # Async operation that may fail transiently
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = await func(*args, **kwargs)

                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{max_attempts}"
                        )

                    return result

                except non_retryable_exceptions as e:
                    # Validation errors - fail immediately, no retry
                    logger.error(
                        f"{func.__name__} failed with non-retryable error: {e}"
                    )
                    raise

                except retryable_exceptions as e:
                    last_exception = e

                    # Last attempt - don't wait, just raise
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        break

                    # Calculate delay and wait
                    delay = exponential_backoff(attempt, backoff_factor, base_delay)
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

            # All attempts exhausted
            raise RetryError(
                f"{func.__name__} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception

        return wrapper
    return decorator


# Common retry configurations for different use cases
def retry_network_operation(max_attempts: int = 3):
    """Retry decorator configured for network operations."""
    import requests
    from urllib3.exceptions import HTTPError

    return retry(
        max_attempts=max_attempts,
        backoff_factor=2.0,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError, HTTPError, requests.RequestException),
        non_retryable_exceptions=(ValueError, TypeError, KeyError)
    )


def retry_file_operation(max_attempts: int = 3):
    """Retry decorator configured for file operations."""
    return retry(
        max_attempts=max_attempts,
        backoff_factor=2.0,
        base_delay=1.0,
        retryable_exceptions=(IOError, OSError, PermissionError),
        non_retryable_exceptions=(ValueError, TypeError, FileNotFoundError)
    )


def retry_database_operation(max_attempts: int = 3):
    """Retry decorator configured for database operations."""
    return retry(
        max_attempts=max_attempts,
        backoff_factor=2.0,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
        non_retryable_exceptions=(ValueError, TypeError, KeyError)
    )


# Example usage
if __name__ == "__main__":
    import random

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Example 1: Basic retry
    @retry(max_attempts=3, backoff_factor=2, base_delay=1)
    def flaky_operation():
        """Simulates an operation that fails randomly."""
        if random.random() < 0.7:
            raise ConnectionError("Network error")
        return "Success!"

    # Example 2: Network operation
    @retry_network_operation(max_attempts=3)
    def fetch_data_from_api():
        """Simulates API call."""
        if random.random() < 0.5:
            raise ConnectionError("API unreachable")
        return {"data": "result"}

    # Example 3: File operation
    @retry_file_operation(max_attempts=3)
    def write_to_locked_file():
        """Simulates writing to a file that may be locked."""
        if random.random() < 0.5:
            raise PermissionError("File is locked")
        return "File written"

    # Test the decorators
    try:
        result = flaky_operation()
        print(f"Operation succeeded: {result}")
    except RetryError as e:
        print(f"Operation failed: {e}")

    try:
        data = fetch_data_from_api()
        print(f"API call succeeded: {data}")
    except RetryError as e:
        print(f"API call failed: {e}")

    try:
        result = write_to_locked_file()
        print(f"File operation succeeded: {result}")
    except RetryError as e:
        print(f"File operation failed: {e}")

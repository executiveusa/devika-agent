"""Service utilities for SYNTHIA.

This module provides utility functions and decorators for service operations,
including retry logic and response validation.

Environment Variables:
    SYNTHIA_MAX_RETRIES: Maximum retry attempts (default: 5)
    SYNTHIA_RETRY_DELAY: Delay between retries in seconds (default: 2)
"""
import sys
import time
import logging
from functools import wraps
from typing import Any, Callable, Optional, Dict
import json

from src.socket_instance import emit_agent

logger = logging.getLogger(__name__)


class InvalidResponseError(Exception):
    """Raised when a response cannot be parsed or is invalid."""
    
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded."""
    
    def __init__(self, attempts: int, last_error: Optional[Exception] = None):
        super().__init__(f"Maximum {attempts} attempts exceeded")
        self.attempts = attempts
        self.last_error = last_error


def retry_wrapper(
    max_tries: int = 5,
    retry_delay: float = 2.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[int, Exception], None]] = None,
):
    """Decorator that adds retry logic to a function.
    
    Args:
        max_tries: Maximum number of retry attempts.
        retry_delay: Delay between retries in seconds.
        on_retry: Optional callback called on each retry with (attempt, exception).
        on_failure: Optional callback called when all retries are exhausted.
    
    Returns:
        Decorated function with retry logic.
    
    Example:
        @retry_wrapper(max_tries=3, retry_delay=1.0)
        def call_api():
            return api.request()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tries = 0
            last_exception: Optional[Exception] = None
            
            while tries < max_tries:
                try:
                    result = func(*args, **kwargs)
                    if result:
                        return result
                    
                    # Empty result is treated as a failure
                    tries += 1
                    if tries < max_tries:
                        logger.warning(
                            f"Empty response from {func.__name__}, "
                            f"retrying ({tries}/{max_tries})..."
                        )
                        emit_agent("info", {
                            "type": "warning",
                            "message": "Empty response, trying again..."
                        })
                        time.sleep(retry_delay)
                        
                except Exception as e:
                    last_exception = e
                    tries += 1
                    
                    if tries < max_tries:
                        logger.warning(
                            f"Error in {func.__name__}: {e}, "
                            f"retrying ({tries}/{max_tries})..."
                        )
                        emit_agent("info", {
                            "type": "warning",
                            "message": f"Error: {str(e)[:100]}, trying again..."
                        })
                        
                        if on_retry:
                            try:
                                on_retry(tries, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback error: {callback_error}")
                        
                        time.sleep(retry_delay)
            
            # All retries exhausted
            error_msg = f"Maximum {max_tries} attempts reached for {func.__name__}"
            logger.error(error_msg)
            emit_agent("info", {
                "type": "error",
                "message": "Maximum attempts reached. Model keeps failing."
            })
            
            if on_failure:
                try:
                    on_failure(max_tries, last_exception)
                except Exception as callback_error:
                    logger.error(f"Failure callback error: {callback_error}")
            
            raise MaxRetriesExceededError(max_tries, last_exception)
        
        return wrapper
    return decorator


def validate_responses(
    strict: bool = False,
    log_attempts: bool = True,
):
    """Decorator that validates and parses JSON responses.
    
    This decorator attempts multiple parsing strategies:
    1. Direct JSON parse
    2. Extract from markdown code blocks
    3. Find JSON object boundaries
    4. Parse line by line
    
    Args:
        strict: If True, raise InvalidResponseError on failure.
                If False, return False on failure.
        log_attempts: If True, log parsing attempts.
    
    Returns:
        Decorated function with response validation.
    
    Example:
        @validate_responses(strict=True)
        def process_response(self, response):
            return response  # response is now parsed JSON
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Convert args to list for modification
            args_list = list(args)
            
            # Expect response as second argument
            if len(args_list) < 2:
                logger.error("validate_responses: expected at least 2 arguments")
                if strict:
                    raise InvalidResponseError("Expected at least 2 arguments")
                return False
            
            response = args_list[1]
            if not isinstance(response, str):
                # Already parsed or different type
                return func(*args_list, **kwargs)
            
            response = response.strip()
            original_response = response
            parse_errors = []
            
            # Strategy 1: Direct JSON parse
            try:
                parsed = json.loads(response)
                if log_attempts:
                    logger.debug(f"Strategy 1 (direct) succeeded for {func.__name__}")
                args_list[1] = parsed
                return func(*args_list, **kwargs)
            except json.JSONDecodeError as e:
                parse_errors.append(f"Direct parse: {e}")
            
            # Strategy 2: Extract from markdown code block
            try:
                if "```" in response:
                    code_block = response.split("```")[1]
                    if code_block:
                        parsed = json.loads(code_block.strip())
                        if log_attempts:
                            logger.debug(f"Strategy 2 (code block) succeeded for {func.__name__}")
                        args_list[1] = parsed
                        return func(*args_list, **kwargs)
            except (IndexError, json.JSONDecodeError) as e:
                parse_errors.append(f"Code block parse: {e}")
            
            # Strategy 3: Find JSON object boundaries
            try:
                start_index = response.find('{')
                end_index = response.rfind('}')
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_str = response[start_index:end_index + 1]
                    parsed = json.loads(json_str)
                    if log_attempts:
                        logger.debug(f"Strategy 3 (boundary) succeeded for {func.__name__}")
                    args_list[1] = parsed
                    return func(*args_list, **kwargs)
            except json.JSONDecodeError as e:
                parse_errors.append(f"Boundary parse: {e}")
            
            # Strategy 4: Parse line by line
            for line in response.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                    if log_attempts:
                        logger.debug(f"Strategy 4 (line-by-line) succeeded for {func.__name__}")
                    args_list[1] = parsed
                    return func(*args_list, **kwargs)
                except json.JSONDecodeError:
                    continue
            
            # All strategies failed
            error_msg = "Failed to parse response as JSON"
            logger.error(
                f"{error_msg} for {func.__name__}. "
                f"Parse errors: {'; '.join(parse_errors)}"
            )
            emit_agent("info", {
                "type": "error",
                "message": error_msg
            })
            
            if strict:
                raise InvalidResponseError(
                    f"{error_msg}. Strategies tried: {'; '.join(parse_errors)}",
                    raw_response=original_response
                )
            
            return False
        
        return wrapper
    return decorator


# Convenience decorators with default settings
def default_retry(func: Callable) -> Callable:
    """Default retry wrapper with 5 attempts."""
    return retry_wrapper(max_tries=5, retry_delay=2.0)(func)


def default_validate(func: Callable) -> Callable:
    """Default response validator (non-strict)."""
    return validate_responses(strict=False, log_attempts=True)(func)

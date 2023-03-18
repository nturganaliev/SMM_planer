import logging
import time
from datetime import datetime

from requests.exceptions import ChunkedEncodingError


def retry_on_network_error(func):
    """Декоратор повторяет запрос к серверу, если произошла ошибка соединения."""

    def wrapper(*args, **kwargs):
        delay = 0
        while True:
            delay = min(delay, 30)
            try:
                return func(*args, **kwargs)
            except (ChunkedEncodingError, ConnectionError):
                time.sleep(delay)
                delay += 5
                continue

    return wrapper


def restart_on_error(func):
    def wrapper(*args, **kwargs):
        logging.basicConfig(
            filename=f'{datetime.now().strftime("%Y-%m-%d %H.%M")}.log',
            level=logging.WARNING
        )
        while True:
            try:
                func(*args, **kwargs)
            except Exception as ex:
                logging.error(f'{datetime.now().strftime("%Y-%m-%d %H.%M.%S")}: {ex}')
                continue

    return wrapper

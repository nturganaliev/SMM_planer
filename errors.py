import time

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

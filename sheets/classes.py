from datetime import datetime
from typing import NamedTuple


class Event(NamedTuple):
    title: str
    text: str
    img_url: str
    posts = []


class Post:

    def __init__(self, service: str, status_field: str, publish_date_raw: str, publish_time_raw: str):
        publish_raw = ' - '.join([publish_date_raw, publish_time_raw])
        self.service = service
        self.status = 'posted' if status_field == 'posted' else 'waiting'
        self.publish_at = datetime.strptime(publish_raw, '%d.%m.%Y - %H:%M:%S')

    def __str__(self):
        return f'{self.service} : {self.publish_at} : {self.status}'

    def is_waiting(self) -> bool:
        return self.status == 'waiting'

from datetime import datetime
from typing import NamedTuple


class Event(NamedTuple):
    line: int
    title: str
    text_url: str
    img_url: str
    posts: list


class Post:

    def __init__(self, social: str, status_field: str, publish_date_raw: str, publish_time_raw: str):
        publish_raw = ' - '.join([publish_date_raw, publish_time_raw])
        self.social = social
        self.status = 'posted' if status_field == 'posted' else 'waiting'
        self.publish_at = datetime.strptime(publish_raw, '%d.%m.%Y - %H:%M:%S')

    def __str__(self):
        return f'{self.social} : {self.publish_at} : {self.status}'


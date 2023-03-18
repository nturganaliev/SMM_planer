from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    line: int
    title: str
    posts: list
    img_url: str
    text_url: str
    text: str = None
    img_file_name: str = None


class Post:

    def __init__(self, social: str, status_field: str, publish_date_raw: str, publish_time_raw: str):
        publish_raw = ' - '.join([publish_date_raw, publish_time_raw])
        self.social = social
        self.status = 'posted' if status_field == 'posted' else 'waiting'
        self.publish_at = datetime.strptime(publish_raw, '%d.%m.%Y - %H:%M:%S')

    def __str__(self):
        return f'{self.social} : {self.publish_at} : {self.status}'


class PlanTableRow:

    def __init__(self, table_row: list):
        if empty_cell_num := 15 - len(table_row):  # добавляем пустые ячейки в конце строки, если нужно
            table_row.extend([''] * empty_cell_num)
        self.title, self.text_url, self.img_url, *vk_tg_ok_ad = table_row
        self.vk_status, self.vk_publish_date, self.vk_publish_time, *tg_ok_ad = vk_tg_ok_ad
        self.tg_status, self.tg_publish_date, self.tg_publish_time, *ok_ad = tg_ok_ad
        self.ok_status, self.ok_publish_date, self.ok_publish_time, *ad = ok_ad
        self.ad_status, self.ad_publish_date, self.ad_publish_time = ad

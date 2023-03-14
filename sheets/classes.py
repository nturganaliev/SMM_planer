from datetime import datetime, date
from typing import NamedTuple


class Post(NamedTuple):
    title: str
    text: str
    img_url: str
    vk_publish_at: datetime
    tg_publish_at: datetime
    ok_publish_at: datetime

    @staticmethod
    def parse_row(input_list: list | tuple):
        vk_publish_datetime = ' - '.join([input_list[3], input_list[4]])
        tg_publish_datetime = ' - '.join([input_list[5], input_list[6]])
        ok_publish_datetime = ' - '.join([input_list[7], input_list[8]])
        return Post(
            title=input_list[0],
            text=input_list[1],
            img_url=input_list[2],
            vk_publish_at=datetime.strptime(vk_publish_datetime, '%d.%m.%Y - %H:%M:%S'),
            tg_publish_at=datetime.strptime(tg_publish_datetime, '%d.%m.%Y - %H:%M:%S'),
            ok_publish_at=datetime.strptime(ok_publish_datetime, '%d.%m.%Y - %H:%M:%S')
        )

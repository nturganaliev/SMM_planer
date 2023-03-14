from datetime import datetime
from typing import NamedTuple


class Post(NamedTuple):
    title: str
    text: str
    img_url: str
    vk_publish_at: datetime
    vk_status: str
    tg_publish_at: datetime
    tg_status: str
    ok_publish_at: datetime
    ok_status: str

    @staticmethod
    def parse_row(input_list: list | tuple):
        def strp_publish_at(datetime_raw: str):
            return datetime.strptime(datetime_raw, '%d.%m.%Y - %H:%M:%S')

        def define_status(input_status: str):
            if not input_status:
                return 'waiting'
            elif input_status == 'posted':
                return 'posted'
            else:
                return 'error'

        vk_publish_datetime = ' - '.join([input_list[4], input_list[5]])
        tg_publish_datetime = ' - '.join([input_list[7], input_list[8]])
        ok_publish_datetime = ' - '.join([input_list[10], input_list[11]])
        return Post(
            title=input_list[0],
            text=input_list[1],
            img_url=input_list[2],
            vk_publish_at=strp_publish_at(vk_publish_datetime),
            vk_status=define_status(input_list[3]),
            tg_publish_at=strp_publish_at(tg_publish_datetime),
            tg_status=define_status(input_list[6]),
            ok_publish_at=strp_publish_at(ok_publish_datetime),
            ok_status=define_status(input_list[9])
        )

    def is_waiting(self) -> bool:
        return any(
            [
                self.vk_status == 'waiting',
                self.tg_status == 'waiting',
                self.ok_status == 'waiting'
            ]
        )

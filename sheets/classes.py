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

    @classmethod
    def parse_row(cls, post_row: list | tuple):
        """
        @post_row: Строка поста из таблицы Google Sheets. Состоит из 12 ячеек:
        Название поста | Текст поста | Ссылка на картинку |
        ВК статус | ВК дата публикации | ВК время публикации |
        ТГ статус | ТГ дата публикации | ТГ время публикации |
        ОК статус | ОК дата публикации | ОК время публикации |
        """
        if len(post_row) != 12:
            raise IndexError

        def strp_publish_at(datetime_raw: str):
            return datetime.strptime(datetime_raw, '%d.%m.%Y - %H:%M:%S')

        def define_status(input_status: str):
            if not input_status:
                return 'waiting'
            elif input_status == 'posted':
                return 'posted'
            else:
                return 'error'

        title, text, img_url, *vk_tg_ok_publishing = post_row
        vk_status, vk_publish_date, vk_publish_time, *tg_ok_publishing = vk_tg_ok_publishing
        tg_status, tg_publish_date, tg_publish_time, *ok_publishing = tg_ok_publishing
        ok_status, ok_publish_date, ok_publish_time = ok_publishing

        return cls(
            title=title,
            text=text,
            img_url=img_url,
            vk_publish_at=strp_publish_at(' - '.join([vk_publish_date, vk_publish_time])),
            vk_status=define_status(vk_status),
            tg_publish_at=strp_publish_at(' - '.join([tg_publish_date, tg_publish_time])),
            tg_status=define_status(tg_status),
            ok_publish_at=strp_publish_at(' - '.join([ok_publish_date, ok_publish_time])),
            ok_status=define_status(ok_status)
        )

    def is_waiting(self) -> bool:
        return any(
            [
                self.vk_status == 'waiting',
                self.tg_status == 'waiting',
                self.ok_status == 'waiting'
            ]
        )

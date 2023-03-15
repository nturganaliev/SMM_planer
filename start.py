import os
import time
from datetime import datetime
from pprint import pprint
from typing import Literal, Iterator

from dotenv import load_dotenv

from sheets.classes import Post
from sheets.methods import get_waiting_posts


def post_on_service(post: Post, service: Literal['vk', 'tg', 'ok']):
    #  Постим на нужных сервисах и отправляем результат в Google Sheets
    if service == 'vk':
        print('VK')
        pprint(post)
    elif service == 'tg':
        print('TG')
        pprint(post)
    elif service == 'ok':
        print('OK')
        pprint(post)


def post_by_status(posts: Iterator[Post]):
    for post in posts:
        if post.vk_status == 'waiting' and post.vk_publish_at <= datetime.now():
            post_on_service(post, service='vk')
        if post.tg_status == 'waiting' and post.tg_publish_at <= datetime.now():
            post_on_service(post, service='tg')
        if post.ok_status == 'waiting' and post.ok_publish_at <= datetime.now():
            post_on_service(post, service='ok')


def main():
    load_dotenv()
    while True:
        # Читаем гугл табличку и запускаем постинг, если надо. В табличке отмечаем сделанное
        posts = get_waiting_posts(
            credentials_file=os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE'],
            spreadsheet_id=os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']
        )
        post_by_status(posts)
        time.sleep(3)


if __name__ == '__main__':
    main()

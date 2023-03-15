import time
from datetime import datetime
from pprint import pprint
from typing import Literal, Iterator

from sheets.classes import Post
from sheets.methods import get_waiting_posts, set_post_statuses, renew_dashboard


def post_on_service(post: Post, service: Literal['vk', 'tg', 'ok']):
    if service == 'vk':
        print('VK')
        pprint(post)
    elif service == 'tg':
        print('TG')
        pprint(post)
    elif service == 'ok':
        print('OK')
        pprint(post)
    else:
        raise ValueError


def post_by_status(posts: Iterator[Post]):
    statuses = {}
    for post in posts:
        if post.vk_status == 'waiting' and post.vk_publish_at <= datetime.now():
            statuses['vk_posting_status'] = post_on_service(post, service='vk')
        if post.tg_status == 'waiting' and post.tg_publish_at <= datetime.now():
            statuses['tg_posting_status'] = post_on_service(post, service='tg')
        if post.ok_status == 'waiting' and post.ok_publish_at <= datetime.now():
            statuses['ok_posting_status'] = post_on_service(post, service='ok')
    set_post_statuses(statuses)
    renew_dashboard()


def main():
    while True:
        posts = get_waiting_posts()
        post_by_status(posts)
        time.sleep(3)


if __name__ == '__main__':
    main()

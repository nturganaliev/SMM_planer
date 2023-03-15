import time
from datetime import datetime
from pprint import pprint

from errors import retry_on_network_error
from sheets.classes import Event
from sheets.methods import get_active_events, renew_dashboard, set_post_status


@retry_on_network_error
def post_by_service(event: Event):
    for post in event.posts:
        if post.service == 'vk' and post.publish_at <= datetime.now():
            set_post_status(event, post.service, 'posted')
            print(event)
            print(post)
        if post.service == 'tg' and post.publish_at <= datetime.now():
            set_post_status(event, post.service, 'posted')
            print(event)
            print(post)
        if post.service == 'ok' and post.publish_at <= datetime.now():
            set_post_status(event, post.service, 'posted')
            print(event)
            print(post)


def main():
    while True:
        events = get_active_events()
        for event in events:
            post_by_service(event)
        renew_dashboard()
        time.sleep(3)


if __name__ == '__main__':
    main()

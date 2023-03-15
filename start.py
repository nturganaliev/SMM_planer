import time
from datetime import datetime

from errors import retry_on_network_error
from sheets.classes import Event
from sheets.methods import get_active_events, renew_dashboard, set_post_status


@retry_on_network_error
def post_by_social(event: Event):
    for post in event.posts:
        now = datetime.now()
        if post.social == 'vk' and post.publish_at <= now:
            set_post_status(event, post.social, 'posted')
        elif post.social == 'tg' and post.publish_at <= now:
            set_post_status(event, post.social, 'posted')
        elif post.social == 'ok' and post.publish_at <= now:
            set_post_status(event, post.social, 'posted')


def main():
    while True:
        events = get_active_events()
        for event in events:
            post_by_social(event)
        renew_dashboard()
        time.sleep(3)


if __name__ == '__main__':
    main()

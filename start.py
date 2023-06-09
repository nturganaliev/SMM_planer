import os
import shutil
from datetime import datetime
from typing import Callable

import pytz
import requests
from googleapiclient.errors import HttpError
from requests import HTTPError
from requests.exceptions import MissingSchema
from telegram.error import BadRequest

from config import TIME_ZONE
from errors import retry_on_network_error, restart_on_error
from helpers import get_img_file_name
from sheets.classes import Event
from sheets.methods import get_active_events, set_post_status, get_post_text, renew_dashboard
from ok.post_to_ok import post_to_ok_group as post_to_ok
from tg.telegram_posting_bot import create_post as post_to_tg
from vk.vk_posting_bot import create_post as post_to_vk


@retry_on_network_error
def post_to_social(post_func: Callable, social: str, event: Event, group_id: int = None):
    post_text = f'{event.title}\n\n{event.text}' if event.text else event.title
    if social == 'ok':
        img_file_path = event.img_url
    else:
        img_file_path = os.path.join('images', event.img_file_name) if event.img_file_name else None

    try:
        is_posted = post_func(post_text, img_file_path, group_id)
        if not is_posted:
            raise ValueError
    except (BadRequest, ValueError, TypeError, KeyError):
        set_post_status(event, social, 'error')
    else:
        set_post_status(event, social, 'posted')


def post_by_social(event: Event):
    for post in event.posts:
        now = datetime.now().astimezone(pytz.timezone(TIME_ZONE))
        if post.social == 'vk' and post.publish_at <= now:
            post_to_social(post_to_vk, post.social, event, group_id=event.vk_group_id)
        if post.social == 'tg' and post.publish_at <= now:
            post_to_social(post_to_tg, post.social, event)
        if post.social == 'ok' and post.publish_at <= now:
            post_to_social(post_to_ok, post.social, event)


@retry_on_network_error
def get_image(img_url: str, img_file_name: str):
    os.makedirs('images', exist_ok=True)
    img_file_path = os.path.join('images', img_file_name)
    response = requests.get(img_url)
    try:
        response.raise_for_status()
    except HTTPError:
        return
    else:
        with open(img_file_path, 'wb') as image_file:
            image_file.write(response.content)


@restart_on_error
def main():
    while True:
        events = get_active_events()
        for event in events:
            if event.text_url:
                try:
                    event.text = get_post_text(event.text_url)
                except (MissingSchema, HTTPError, HttpError):
                    set_post_status(event, ['vk', 'tg', 'ok'], 'error')
                    continue
            if event.img_url:
                try:
                    event.img_file_name = get_img_file_name(event.img_url)
                    get_image(event.img_url, event.img_file_name)
                except (MissingSchema, HTTPError):
                    set_post_status(event, ['vk', 'tg', 'ok'], 'error')
                    continue
            post_by_social(event)
        shutil.rmtree('images', ignore_errors=True)
        renew_dashboard()


if __name__ == '__main__':
    main()

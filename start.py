import os
import shutil
import time
from datetime import datetime
from typing import Callable
from urllib.parse import urlparse

import requests
from googleapiclient.errors import HttpError
from requests import HTTPError
from requests.exceptions import MissingSchema
from telegram.error import BadRequest

from errors import retry_on_network_error
from sheets.classes import Event
from sheets.methods import get_events, renew_dashboard, set_post_status, get_post_text
from ok.post_to_ok import post_to_ok_group as post_to_ok
from tg.telegram_posting_bot import create_post as post_to_tg
from vk.vk_posting_bot import create_post as post_to_vk


@retry_on_network_error
def post_to_social(post_func: Callable, post_text: str, social: str, event: Event):
    img_file_path = os.path.join('images', event.img_file_name) if event.img_file_name else None
    try:
        is_posted = post_func(post_text, img_file_path)
        if not is_posted:
            raise ValueError
    except (BadRequest, ValueError, TypeError):
        set_post_status(event, social, 'error')
    else:
        set_post_status(event, social, 'posted')


def post_by_social(event: Event):
    post_text = f'{event.title}\n\n{event.text}' if event.text else event.title
    for post in event.posts:
        now = datetime.now()
        if post.social == 'vk' and post.publish_at <= now:
            post_to_social(post_to_vk, post_text, post.social, event)
        if post.social == 'tg' and post.publish_at <= now:
            post_to_social(post_to_tg, post_text, post.social, event)
        # if post.social == 'ok' and post.publish_at <= now:
        #     post_to_social(post_to_ok, post_text, post.social, event)


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


def get_img_file_name(img_url: str) -> str:
    parsed_url = urlparse(img_url)
    return parsed_url.path.split('/')[-1]


def main():
    while True:
        events = get_events()
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
        renew_dashboard()
        shutil.rmtree('images', ignore_errors=True)
        time.sleep(3)


if __name__ == '__main__':
    main()

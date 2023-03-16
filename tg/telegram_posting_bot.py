import os

import telegram
from dotenv import load_dotenv


def create_post(post_text, post_image=False, telegram_channel=None):
    load_dotenv('.env')
    if not telegram_channel:
        telegram_channel = os.environ['TELEGRAM_CHANNEL']
    telegram_bot_token = os.environ['TELEGRAM_TOKEN']
    telegram_bot = telegram.Bot(token=telegram_bot_token)
    if post_image:
        with open(os.path.join('images', post_image), 'rb') as image:
            telegram_bot.send_photo(
                chat_id=telegram_channel,
                photo=image,
                caption=post_text
            )
    else:
        telegram_bot.send_message(
            chat_id=telegram_channel,
            text=post_text
        )
    return True

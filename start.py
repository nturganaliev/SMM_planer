import time
from pprint import pprint

from sheets.methods import get_waiting_posts
import config


def main():
    while True:
        # Читаем гугл табличку и запускаем постинг, если надо. В табличке отмечаем сделанное
        posts = get_waiting_posts(
            credentials_file=config.credentials_file,
            spreadsheet_id=config.spreadsheet_id
        )
        for post in posts:
            pprint(post)
        time.sleep(5)


if __name__ == '__main__':
    main()

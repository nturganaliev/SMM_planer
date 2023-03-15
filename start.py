import os
import time
from pprint import pprint

from dotenv import load_dotenv

from sheets.methods import get_waiting_posts


def main():
    load_dotenv()
    while True:
        # Читаем гугл табличку и запускаем постинг, если надо. В табличке отмечаем сделанное
        posts = get_waiting_posts(
            credentials_file=os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE'],
            spreadsheet_id=os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']
        )
        for post in posts:
            pprint(post)
        time.sleep(5)


if __name__ == '__main__':
    main()

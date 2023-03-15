import os
from typing import Iterator

import httplib2
import apiclient
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

from errors import retry_on_network_error
from .classes import Post

load_dotenv()
_credentials_file = os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE']
_spreadsheet_id = os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']


@retry_on_network_error
def login():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        _credentials_file,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build('sheets', 'v4', http=httpAuth)


@retry_on_network_error
def get_waiting_posts() -> Iterator[Post]:
    service = login(_credentials_file)
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A3:L10000',
        majorDimension='ROWS'
    ).execute()
    all_posts = get_all_posts(plan_table['values'])
    return filter(lambda post: post.is_waiting(), all_posts)


def get_all_posts(posts_rows: list[list]) -> Iterator[Post]:
    for post in posts_rows:
        try:
            post = Post.parse_row(post)
        except (IndexError, ValueError) as ex:
            print(ex)
        else:
            yield post


@retry_on_network_error
def set_post_statuses(statuses: dict):
    service = login()
    pass


@retry_on_network_error
def renew_dashboard():
    service = login()
    pass

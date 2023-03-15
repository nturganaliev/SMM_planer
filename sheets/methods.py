from pprint import pprint
from typing import Iterator

import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

from errors import retry_on_network_error
from .classes import Post


@retry_on_network_error
def login(credentials_file: str):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        credentials_file,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build('sheets', 'v4', http=httpAuth)


@retry_on_network_error
def get_waiting_posts(credentials_file: str, spreadsheet_id: str) -> Iterator[Post]:
    service = login(credentials_file)
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Plan!A3:L10000',
        majorDimension='ROWS'
    ).execute()
    all_posts = get_all_posts(plan_table['values'])
    return filter(lambda post: post.is_waiting(), all_posts)


def get_all_posts(posts_rows):
    for post in posts_rows:
        try:
            post = Post.parse_row(post)
        except (IndexError, ValueError):
            continue
        else:
            yield post

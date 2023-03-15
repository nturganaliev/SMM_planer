import os
from pprint import pprint
from typing import Iterator

import httplib2
import apiclient
from dotenv import load_dotenv
from google.api.service_pb2 import Service
from oauth2client.service_account import ServiceAccountCredentials

from errors import retry_on_network_error
from .classes import Event, Post

load_dotenv()
_credentials_file = os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE']
_spreadsheet_id = os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']


@retry_on_network_error
def login() -> Service:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        _credentials_file,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    http_auth = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build('sheets', 'v4', http=http_auth)


@retry_on_network_error
def get_active_events() -> Iterator[Event]:
    service = login()
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A3:L10000',
        majorDimension='ROWS'
    ).execute()
    return parse_table_rows(plan_table['values'])


@retry_on_network_error
def set_post_status(event: Event, social: str, status: str):
    service = login()

    status_columns = {'vk': 'D', 'tg': 'G', 'ok': 'J'}
    column = status_columns[social]
    range_ = f'Plan!{column}{event.line + 3}:{column}{event.line + 3}'

    service.spreadsheets().values().batchUpdate(spreadsheetId=_spreadsheet_id, body={
        'valueInputOption': 'USER_ENTERED',
        'data': {
            'range': range_,
            'majorDimension': 'ROWS',
            'values': [[status]]}
    }).execute()


@retry_on_network_error
def renew_dashboard():
    service = login()
    pass


def parse_table_rows(table_rows: list[list]) -> Iterator[Event]:
    for row_num, row in enumerate(table_rows):
        if empty_cell_num := 12 - len(row):  # добавляем пустые ячейки в конце строки, если нужно
            row.extend([''] * empty_cell_num)
        title, text, img_url, *vk_tg_ok_publishing = row
        vk_status, vk_publish_date, vk_publish_time, *tg_ok_publishing = vk_tg_ok_publishing
        tg_status, tg_publish_date, tg_publish_time, *ok_publishing = tg_ok_publishing
        ok_status, ok_publish_date, ok_publish_time = ok_publishing

        event = Event(line=row_num, title=title, text=text, img_url=img_url, posts=list())
        if not vk_status == 'posted':
            add_post_to_event(
                event,
                social='vk',
                status_field=vk_status,
                publish_date_raw=vk_publish_date,
                publish_time_raw=vk_publish_time
            )
        if not tg_status == 'posted':
            add_post_to_event(
                event,
                social='tg',
                status_field=tg_status,
                publish_date_raw=tg_publish_date,
                publish_time_raw=tg_publish_time
            )
        if not ok_status == 'posted':
            add_post_to_event(
                event,
                social='ok',
                status_field=ok_status,
                publish_date_raw=ok_publish_date,
                publish_time_raw=ok_publish_time
            )
        if event.posts:
            print(event, event.posts)
            yield event


def add_post_to_event(
        event: Event,
        social: str,
        status_field: str,
        publish_date_raw: str,
        publish_time_raw: str):
    try:
        post = Post(
            social=social,
            status_field=status_field,
            publish_date_raw=publish_date_raw,
            publish_time_raw=publish_time_raw
        )
    except ValueError:
        set_post_status(event, social, 'error')
    else:
        if status_field == 'error':
            set_post_status(event, social, '')
        event.posts.append(post)

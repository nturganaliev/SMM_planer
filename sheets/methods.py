import json
import os
from pprint import pprint
from typing import Iterator
from urllib.parse import urlparse

import httplib2
import apiclient
from dotenv import load_dotenv
from google.api.service_pb2 import Service
from oauth2client.service_account import ServiceAccountCredentials

from errors import retry_on_network_error
from .classes import Event, Post
from .parse_google_doc import read_structural_elements

load_dotenv()
_credentials_file = os.environ['GOOGLE_SHEETS_CREDENTIALS_FILE']
_spreadsheet_id = os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']


@retry_on_network_error
def login(service_name: str, version: str) -> Service:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        _credentials_file,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/documents.readonly',
         'https://www.googleapis.com/auth/drive'])
    http_auth = credentials.authorize(httplib2.Http())
    return apiclient.discovery.build(service_name, version, http=http_auth)


@retry_on_network_error
def get_events() -> Iterator[Event]:
    service = login('sheets', version='v4')
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A1:L10000',
        majorDimension='ROWS'
    ).execute()
    return parse_events_from_plan(plan_table['values'])


@retry_on_network_error
def get_post_text(text_url: str) -> str:
    service = login('docs', version='v1')
    parsed_url = urlparse(text_url)
    document_id = parsed_url.path.lstrip('/document/d/').split('/')[0]
    document = service.documents().get(documentId=document_id).execute()
    with open('doc.json', 'w') as file:
        json.dump(document, file)
    return read_structural_elements(document.get('body').get('content'))


@retry_on_network_error
def set_post_status(event: Event, socials: str | list | tuple, status: str):
    service = login('sheets', version='v4')
    status_columns = {'vk': 'D', 'tg': 'G', 'ok': 'J'}
    if isinstance(socials, str):
        socials = [socials]

    data = []
    for socials in socials:
        column = status_columns[socials]
        data.append(
            {
                'range': f'Plan!{column}{event.line}:{column}{event.line}',
                'majorDimension': 'ROWS',
                'values': [[status]]
            }
        )

    service.spreadsheets().values().batchUpdate(spreadsheetId=_spreadsheet_id, body={
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }).execute()


@retry_on_network_error
def renew_dashboard():
    service = login('sheets', version='v4')
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A1:L10000',
        majorDimension='ROWS'
    ).execute()
    events = parse_events_from_plan(plan_table['values'])
    data = []
    sheet_requests = []
    for event in events:
        statuses = {
            post.social: post.status
            for post in event.posts
        }
        first_row = (event.line - 2) * 3 - 1

        data.append(
            {
                'range': f'Dashboard!A{first_row}:B{first_row + 2}',
                'majorDimension': 'ROWS',
                'values': [
                    [event.title, 'VK'],
                    ['', 'TG'],
                    ['', 'OK']
                ]
            }
        )
        sheet_requests.append(
            {"mergeCells": {"range": {'sheetId': 737766278,
                                      'startRowIndex': first_row - 1,
                                      'endRowIndex': first_row + 2,
                                      'startColumnIndex': 0,
                                      'endColumnIndex': 1},
                            "mergeType": 'MERGE_COLUMNS'}})
        # sheet_requests.append(
        #     {'updateCells':
        #          {"range": {'sheetId': 737766278,
        #                     'startRowIndex': first_row - 1,
        #                     'endRowIndex': first_row + 2,
        #                     'startColumnIndex': 0,
        #                     'endColumnIndex': 1},
        #           'rows': [{'values': [{'userEnteredFormat': {'backgroundColor': {'red': 1, 'green': 0, 'blue': 0}}},
        #                                {'userEnteredFormat': {'backgroundColor': {'red': 0, 'green': 1, 'blue': 0}}}]},
        #                    {'values': [{'userEnteredFormat': {'backgroundColor': {'red': 0, 'green': 0, 'blue': 1}}},
        #                                {'userEnteredFormat': {'backgroundColor': {'red': 1, 'green': 1, 'blue': 0}}}]}],
        #           'fields': 'userEnteredFormat'}})

        # pprint(sheet_requests)
        service.spreadsheets().values().batchUpdate(spreadsheetId=_spreadsheet_id, body={
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }).execute()
        service.spreadsheets().batchUpdate(
            spreadsheetId=_spreadsheet_id,
            body={
                "requests": sheet_requests
            }
        ).execute()


def parse_events_from_plan(table_rows: list[list]) -> Iterator[Event]:
    for row_num, row in enumerate(table_rows[2:], start=3):
        if empty_cell_num := 12 - len(row):  # добавляем пустые ячейки в конце строки, если нужно
            row.extend([''] * empty_cell_num)
        title, text_url, img_url, *vk_tg_ok_publishing = row
        if not title:
            continue
        vk_status, vk_publish_date, vk_publish_time, *tg_ok_publishing = vk_tg_ok_publishing
        tg_status, tg_publish_date, tg_publish_time, *ok_publishing = tg_ok_publishing
        ok_status, ok_publish_date, ok_publish_time = ok_publishing

        event = Event(line=row_num, title=title, img_url=img_url, posts=list(), text_url=text_url)
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

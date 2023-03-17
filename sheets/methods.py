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
from .classes import Event, Post, PlanTableRow
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
    if len(plan_table) > 2:
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
    dashboard_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Dashboard!A1:B10000',
        majorDimension='ROWS'
    ).execute()
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A1:L10000',
        majorDimension='ROWS'
    ).execute()
    if len(plan_table) < 2:
        return

    plan_headers_number = 2
    dashboard_headers_number = 1
    socials_number = 3

    batch_update = []
    sheet_requests = []
    for row_number, row in enumerate(plan_table['values'][2:], start=3):
        parsed_row = PlanTableRow(row)
        if not parsed_row.title:
            continue
        statuses = {'VK': parsed_row.vk_status,
                    'TG': parsed_row.tg_status,
                    'OK': parsed_row.ok_status}
        title_row_on_dashboard = (row_number - plan_headers_number) * socials_number - dashboard_headers_number

        batch_update.append(
            {'range': f'Dashboard!A{title_row_on_dashboard}:B{title_row_on_dashboard + socials_number - 1}',
             'majorDimension': 'ROWS',
             'values': [[parsed_row.title, 'VK'],
                        ['', 'TG'],
                        ['', 'OK']]})
        sheet_requests.append(
            {"mergeCells": {"range": {'sheetId': 737766278,
                                      'startRowIndex': title_row_on_dashboard - dashboard_headers_number,
                                      'endRowIndex': title_row_on_dashboard + socials_number - 1,
                                      'startColumnIndex': 0,
                                      'endColumnIndex': 1},
                            "mergeType": 'MERGE_COLUMNS'}})

    service.spreadsheets().values().batchUpdate(spreadsheetId=_spreadsheet_id, body={
        'valueInputOption': 'USER_ENTERED',
        'data': batch_update
    }).execute()
    service.spreadsheets().batchUpdate(
        spreadsheetId=_spreadsheet_id,
        body={
            "requests": sheet_requests
        }
    ).execute()

    len_dashboard = len(dashboard_table) - dashboard_headers_number
    len_plan = (len(plan_table) - plan_headers_number)
    if len_dashboard > len_plan * socials_number:
        pass  # чистить не нужные строки в dashboard


def parse_events_from_plan(table_rows: list[list]) -> Iterator[Event]:
    for row_num, table_row in enumerate(table_rows[2:], start=3):

        row = PlanTableRow(table_row)
        if not row.title:
            continue

        event = Event(line=row_num, title=row.title, img_url=row.img_url, posts=list(), text_url=row.text_url)
        if not row.vk_status == 'posted':
            add_post_to_event(
                event,
                social='vk',
                status_field=row.vk_status,
                publish_date_raw=row.vk_publish_date,
                publish_time_raw=row.vk_publish_time
            )
        if not row.tg_status == 'posted':
            add_post_to_event(
                event,
                social='tg',
                status_field=row.tg_status,
                publish_date_raw=row.tg_publish_date,
                publish_time_raw=row.tg_publish_time
            )
        if not row.ok_status == 'posted':
            add_post_to_event(
                event,
                social='ok',
                status_field=row.ok_status,
                publish_date_raw=row.ok_publish_date,
                publish_time_raw=row.ok_publish_time
            )
        if event.posts:
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

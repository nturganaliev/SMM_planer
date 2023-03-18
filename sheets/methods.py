import os
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
def get_active_events() -> Iterator[Event]:
    service = login('sheets', version='v4')
    plan_table = service.spreadsheets().values().get(
        spreadsheetId=_spreadsheet_id,
        range='Plan!A1:M10000',
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
    return read_structural_elements(document.get('body').get('content'))


@retry_on_network_error
def set_post_status(event: Event, socials: str | list | tuple, status: str):
    service = login('sheets', version='v4')
    status_columns = {'vk': 'D', 'tg': 'G', 'ok': 'J', 'ad_тг': 'M', 'ad_ок': 'M', 'ad_вк': 'M'}
    if isinstance(socials, str):
        socials = [socials]

    data = []
    for socials in socials:
        column = status_columns[socials]
        data.append({'range': f'Plan!{column}{event.line}:{column}{event.line}',
                     'majorDimension': 'ROWS',
                     'values': [[status]]})

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=_spreadsheet_id,
        body={'valueInputOption': 'USER_ENTERED',
              'data': data}
    ).execute()
    renew_dashboard()


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
        range='Plan!A1:M10000',
        majorDimension='ROWS'
    ).execute()
    if len(plan_table) < 2:
        return

    sheet_id = 737766278
    plan_headers_number = 2
    dashboard_headers_number = 1
    socials_number = 3
    index_correction = 1
    title_column = 0
    socials_column = 1
    events_in_dashboard = (len(dashboard_table['values']) - dashboard_headers_number) / socials_number
    events_in_plan = count_events_in_plan(plan_table['values'][plan_headers_number:])
    background_colors = {
        'normal': {'red': 1, 'green': 0.95, 'blue': 0.8},
        'error': {'red': 1, 'green': 0.5, 'blue': 0.5},
        'posted': {'red': 0.5, 'green': 1, 'blue': 0.5},
        '': {'red': 0.3, 'green': 0.6, 'blue': 1}  # waiting
    }

    batch_update = []
    formatting_requests = []
    for row_number_in_plan, row in enumerate(plan_table['values'][2:], start=plan_headers_number):
        parsed_row = PlanTableRow(row)
        if not parsed_row.title:
            continue

        post_row_on_dashboard = (row_number_in_plan - plan_headers_number) * socials_number \
                                + dashboard_headers_number + index_correction

        title_range = {'sheetId': sheet_id,
                       'startRowIndex': post_row_on_dashboard - dashboard_headers_number,
                       'endRowIndex': post_row_on_dashboard + socials_number - index_correction,
                       'startColumnIndex': title_column,
                       'endColumnIndex': title_column + index_correction}
        socials_range = {'sheetId': sheet_id,
                         'startRowIndex': post_row_on_dashboard - dashboard_headers_number,
                         'endRowIndex': post_row_on_dashboard - dashboard_headers_number + socials_number + index_correction,
                         'startColumnIndex': socials_column,
                         'endColumnIndex': socials_column + index_correction}

        batch_update.append(
            {'range': f'Dashboard!A{post_row_on_dashboard}:'
                      f'B{post_row_on_dashboard + socials_number - index_correction}',
             'majorDimension': 'ROWS',
             'values': [[parsed_row.title, 'VK'],
                        ['', 'TG'],
                        ['', 'OK']]})

        formatting_requests.extend([
            {"mergeCells": {"range": title_range,
                            "mergeType": 'MERGE_COLUMNS'}},
            {'repeatCell': {'range': title_range,
                            'cell': {'userEnteredFormat': {'verticalAlignment': 'TOP',
                                                           'textFormat': {'bold': True},
                                                           'backgroundColor': background_colors['normal']}},
                            'fields': 'userEnteredFormat'}}])
        formatting_requests.append(
            {'updateCells': {
                'range': socials_range,
                'rows': [
                    {'values': [{'userEnteredFormat': {'backgroundColor': background_colors[parsed_row.vk_status]}}]},
                    {'values': [{'userEnteredFormat': {'backgroundColor': background_colors[parsed_row.tg_status]}}]},
                    {'values': [{'userEnteredFormat': {'backgroundColor': background_colors[parsed_row.ok_status]}}]}
                ],
                'fields': 'userEnteredFormat'}})

    if events_in_dashboard > events_in_plan:
        start_index = events_in_plan * socials_number + dashboard_headers_number
        formatting_requests.append({
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_index,
                    "endIndex": start_index + 30}}})

    service.spreadsheets().values().batchUpdate(spreadsheetId=_spreadsheet_id, body={
        'valueInputOption': 'USER_ENTERED',
        'data': batch_update
    }).execute()

    service.spreadsheets().batchUpdate(
        spreadsheetId=_spreadsheet_id,
        body={
            "requests": formatting_requests
        }
    ).execute()


def parse_events_from_plan(table_rows: list[list]) -> Iterator[Event]:
    vk_groups = {'ВК группа 1': os.getenv('VK_GROUP_ID1'), 'ВК группа 2': os.getenv('VK_GROUP_ID2')}

    for row_num, table_row in enumerate(table_rows[2:], start=3):

        parsed_row = PlanTableRow(table_row)

        event = Event(
            line=row_num,
            title=parsed_row.title,
            img_url=parsed_row.img_url,
            text_url=parsed_row.text_url,
            vk_group_id=vk_groups.get(parsed_row.vk_group),
            posts=list())

        if not event.title:
            set_post_status(event, ['vk', 'tg', 'ok'], '')
            continue

        if not parsed_row.vk_status == 'posted':
            add_post_to_event(
                event,
                social='vk',
                status_field=parsed_row.vk_status,
                publish_date_raw=parsed_row.vk_publish_date,
                publish_time_raw=parsed_row.vk_publish_time)
        if not parsed_row.tg_status == 'posted':
            add_post_to_event(
                event,
                social='tg',
                status_field=parsed_row.tg_status,
                publish_date_raw=parsed_row.tg_publish_date,
                publish_time_raw=parsed_row.tg_publish_time)
        if not parsed_row.ok_status == 'posted':
            add_post_to_event(
                event,
                social='ok',
                status_field=parsed_row.ok_status,
                publish_date_raw=parsed_row.ok_publish_date,
                publish_time_raw=parsed_row.ok_publish_time)
        if event.posts:
            yield event


def add_post_to_event(
        event: Event,
        social: str,
        status_field: str,
        publish_date_raw: str,
        publish_time_raw: str
):
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
        if check_urls(event.img_url) and check_urls(event.text_url) and status_field == 'error':
            set_post_status(event, social, '')
        event.posts.append(post)


def count_events_in_plan(rows: list[list]) -> int:
    count = 0
    for row in rows:
        try:
            title = row[0]
        except IndexError:
            continue
        else:
            if title:
                count += 1
    return count


def check_urls(url):
    if not url or url.startswith('http'):
        return True

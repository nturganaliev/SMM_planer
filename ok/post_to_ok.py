import os
import hashlib
import json
import requests

from dotenv import load_dotenv
from pathlib import Path


def get_ok_upload_server_url_and_photo_ids(
        app_key,
        gid,
        access_token,
        session_secret_key
    ):
    url = 'https://api.ok.ru/fb.do'
    data = "application_key={}gid={}\
        method=photosV2.getUploadUrlsession_key={}{}"\
        .format(app_key, gid, access_token, session_secret_key)
    signature = hashlib.md5(bytes(data, encoding='utf-8')).hexdigest()
    params = {
        "application_key": app_key,
        "gid": gid,
        "method": "photosV2.getUploadUrl",
        "session_key": access_token,
        "sig": signature
    }
    response = requests.get(url, params)
    response.raise_for_status()
    content = response.json()
    upload_url = content['upload_url']
    photo_ids = content['photo_ids']

    return upload_url, photo_ids


def upload_photo_to_ok_server(upload_url, photo):
    with open(photo, 'rb') as file:
        image = {
            "photo": file,
            "content-type": "multipart/form-data"
        }
        response = requests.post(upload_url, files=image)
    response.raise_for_status()
    return response.json()


def save_photo_on_ok_album(app_key, gid, photo_id, access_token, image_token):
    url = 'https://api.ok.ru/fb.do'
    data = "application_key={}method=photosV2.commitphoto_id={}\
            session_key={}token={}"\
            .format(app_key, photo_id, access_token, image_token)
    signature = hashlib.md5(bytes(data, encoding='utf-8')).hexdigest()
    params = {
        'application_key': app_key,
        'gid': gid,
        'method': 'photosV2.commit',
        'photo_id': photo_id,
        'session_key': access_token,
        'token': image_token,
        'sig': signature
    }
    response = requests.post(url, params)
    response.raise_for_status()
    return response.json()


def post_to_ok_group(text, photo):
    load_dotenv()
    app_id = os.getenv('AID')
    app_key = os.getenv('APP_PUBLIC_KEY')
    app_secret_key = os.getenv('APP_SECRET_KEY')
    gid = os.getenv('GID')
    access_token = os.getenv('ACCESS_TOKEN')
    session_secret_key = os.getenv('SESSION_SECRET_KEY')
    url = 'https://api.ok.ru/fb.do'

    try:
        upload_url, photo_ids = get_ok_upload_server_url_and_photo_ids(
                                    app_key,
                                    gid,
                                    access_token,
                                    session_secret_key)
    except requests.exceptions.RequestException as error:
        print(error)
        return

    try:
        upload_content = upload_photo_to_ok_server(upload_url, photo)
    except requests.exceptions.RequestException as error:
        print(error)
        return

    image_token = upload_content['photos'][photo_ids[0]]['token']
    photos_info = save_photo_on_ok_album(
        app_key,
        gid,
        photo_ids,
        access_token,
        image_token
    )
    photo_id = photos_info['photos'][0]['assigned_photo_id']

    media = json.dumps({
        "media": [
            {
                "type": "text",
                "text": text,
            },
            {
                "type": "photo",
                "list": [
                    { "id": image_token, },
                    {"photoId": photo_id,},
                ]
            },
        ],
    })

    data = "application_key={}attachment={}\
            method=mediatopic.postsession_key={}"\
            .format(app_key, media, access_token)
    signature = hashlib.md5(bytes(data, encoding='utf-8')).hexdigest()
    params = {
        'application_key': app_key,
        'attachment': media,
        'method': 'mediatopic.post',
        'session_key': access_token,
        'sig': signature
    }

    response = requests.post(url, params)
    response.raise_for_status()
    print(response.json())
    return response.json()


def main():
    parent_dirpath = Path(os.path.abspath('.')).parent.absolute()
    filepath = os.path.join(parent_dirpath, 'images', 'man.jpg')
    text = 'Hello'
    post_to_ok_group(text, filepath)


if __name__ == '__main__':
    main()

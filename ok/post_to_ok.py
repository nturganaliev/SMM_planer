import os
import hashlib
import json
import requests

from dotenv import load_dotenv


def post_to_ok_group(text, photo_url=None, gid=None):
    load_dotenv('.env')
    app_key = os.getenv('APP_KEY')
    access_token = os.getenv('ACCESS_TOKEN')
    if not gid:
        gid = os.getenv('GID')
    post_type=os.getenv('POST_TYPE')
    session_secret_key = os.getenv('SESSION_SECRET_KEY')
    url = 'https://api.ok.ru/fb.do'
    if not photo_url:
        attachement = json.dumps({"media": [{"type": "text", "text": text,}]})
    else:
        attachement = json.dumps({
            "media": [
                {"type": "text", "text": text},
                {"type": "link", "url": photo_url}
            ],
        })
    data = "application_key={}"\
           "attachement={}"\
           "gid={}"\
           "method=mediatopic.post"\
           "type={}"\
           "session_secret_key={}"\
            .format(
                app_key,
                attachement,
                gid,
                post_type,
                session_secret_key
            )
    signature = hashlib.md5(
        bytes(data, encoding='utf-8')
    ).hexdigest()
    params = {
        'application_key': app_key,
        'method': 'mediatopic.post',
        'gid': gid,
        'type': post_type,
        'attachment': attachement,
        'access_token': access_token,
        'signature': signature
    }
    response = requests.post(url, params)
    response.raise_for_status()
    return response.json()


def main():
    text = "Hello world!"
    photo_url = "https://burst.shopify.com/photos"\
                "/person-holds-a-book-over-a-stack-"\
                "and-turns-the-page/download"
    try:
        print("Posting...")
        result = post_to_ok_group(text, photo_url)
        print("Successful!")
    except requests.exceptions.RequestException as error:
        print(error)
        return

if __name__ == '__main__':
    main()
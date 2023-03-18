from urllib.parse import urlparse


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


def get_img_file_name(img_url: str) -> str:
    parsed_url = urlparse(img_url)
    return parsed_url.path.split('/')[-1]

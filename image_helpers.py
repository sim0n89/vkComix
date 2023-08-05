from os.path import splitext
from pathlib import Path
from urllib import parse

import requests


def get_image_extension(url):
    path = parse.urlparse(url)
    return splitext(path.path.rstrip("/").split("/")[-1])[-1]


def save_image(url, name, params=None):
    path = Path("images")
    path.mkdir(exist_ok=True)
    file_path = path / name
    response = requests.get(url, params=params)
    response.raise_for_status()
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path
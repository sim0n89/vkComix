import json
from os.path import dirname, join
from pathlib import Path
from random import randrange

import requests
from dotenv import load_dotenv

from image_helpers import *
from vk_methods import *


def download_comix(url):
    response = requests.get(url)
    response.raise_for_status()
    comix = response.json()
    return comix


def save_comix(comix, comix_id):
    path = Path("files")
    path.mkdir(exist_ok=True)
    name = f"{comix_id}.json"
    file_path = path / name
    with open(file_path, "w") as file:
        json.dump(comix, file)
    return file_path


def main():
    current_comix = download_comix("https://xkcd.com/info.0.json")
    last_comix = current_comix["num"]
    comix_id = randrange(1, last_comix)
    try:
        url = f"https://xkcd.com/{comix_id}/info.0.json"
        comix = download_comix(url)
    except requests.HTTPError as e:
        print(e)

    image_url = comix["img"]
    extension = get_image_extension(image_url)
    image_name = f"{comix_id}{extension}"
    image_path = save_image(image_url, image_name)
    comix_path = save_comix(comix, comix_id)
    try:
        saved_image = save_wall_photo(image_path)
    except HTTPError as e:
        exit(e)

    public_post(saved_image, comix["alt"])
    Path.unlink(image_path)
    Path.unlink(comix_path)


if __name__ == "__main__":
    main()

import json
import os
from os.path import dirname, join
from pathlib import Path
from random import randrange
from pprint import pprint
import requests
from dotenv import load_dotenv

from image_helpers import get_image_extension, save_image


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


def download_random_comix():
    current_comix = download_comix("https://xkcd.com/info.0.json")
    last_comix = current_comix["num"]
    comix_id = randrange(1, last_comix)
    url = f"https://xkcd.com/{comix_id}/info.0.json"
    comix = download_comix(url)
    return comix


def get_upload_fields(access_token, group_id):
    params = {"group_id": group_id, "access_token": access_token, "v": 5.131}
    response = requests.get(
        f"https://api.vk.com/method/photos.getWallUploadServer", params=params
    )
    response.raise_for_status()
    response = response.json()
    return response["response"]


def send_photo(upload_fields, image_path, group_id, access_token):
    with open(image_path, "rb") as file:
        url = upload_fields["upload_url"]
        files = {
            "file": file,  # Вместо ключа "media" скорее всего нужно подставить другое название ключа. Какое конкретно см. в доке API ВК.
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        uploaded_file = response.json()
    if uploaded_file["photo"] != "":
        uploaded_file["group_id"] = group_id
        uploaded_file["access_token"] = access_token
        uploaded_file["v"] = 5.131
        response_image = requests.post(
            "https://api.vk.com/method/photos.saveWallPhoto", params=uploaded_file
        )
        response_image.raise_for_status()
        saved_image = response_image.json()
        return saved_image["response"]


def publish_post(saved_image, text, group_id, access_token):
    media_id = saved_image[0]["id"]
    image_owner_id = saved_image[0]["owner_id"]
    owner_id = f"-{group_id}"
    attachments = f"photo{image_owner_id}_{media_id}"
    params = {
        "attachments": attachments, 
        "message": text, 
        "owner_id": owner_id,
        "access_token":access_token,
        "v":5.131
        }
    response = requests.post("https://api.vk.com/method/wall.post", params=params)
    response.raise_for_status()
    return response.json()


def main():
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    try:
        access_token = os.environ["ACCESS_TOKEN"]
    except KeyError as e:
        print("Вы не указали ACCESS_TOKEN")
        return

    try:
        group_id = os.environ["GROUP_ID"]
    except KeyError as e:
        print("Вы не указали GROUP_ID")
        return

    try:
        app_id = os.environ["APP_ID"]
    except KeyError as e:
        print("Вы не указали APP_ID")
        return

    try:
        comix = download_random_comix()
    except requests.HTTPError as e:
        print(e)
    comix_id = comix["num"]
    comix_text = comix["alt"]
    image_url = comix["img"]
    extension = get_image_extension(image_url)
    image_name = f"{comix_id}{extension}"
    image_path = save_image(image_url, image_name)
    comix_path = save_comix(comix, comix_id)
    try:
        server_address = get_upload_fields(access_token, group_id)
    except requests.HTTPError as e:
        print(e)
        return

    try:
        saved_image = send_photo(server_address, image_path, group_id, access_token)
    except requests.HTTPError as e:
        print(e)
        return
    finally:
        Path.unlink(image_path)
        Path.unlink(comix_path)

    try:
        post = publish_post(saved_image, comix_text, group_id, access_token)
    except requests.HTTPError as e:
        print(e)
        return


if __name__ == "__main__":
    main()

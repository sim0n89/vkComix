import os
from os.path import dirname, join
from pathlib import Path
from random import randrange
from pprint import pprint
import requests
from dotenv import load_dotenv

from image_helpers import get_image_extension, save_image


def download_random_comix():
    response_num_comix = requests.get("https://xkcd.com/info.0.json")
    response_num_comix = response_num_comix.json()
    count_comixes = response_num_comix["num"]
    comix_id = randrange(1, count_comixes)

    url = f"https://xkcd.com/{comix_id}/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    comix = response.json()

    comix_id = comix["num"]
    comix_text = comix["alt"]
    image_url = comix["img"]
    extension = get_image_extension(image_url)
    image_name = f"{comix_id}{extension}"
    image_path = save_image(image_url, image_name)
    saved_comix = {"image_path": image_path, "text": comix_text}
    return saved_comix


def get_upload_url(vk_token, group_id):
    params = {"group_id": group_id, "access_token": vk_token, "v": 5.131}
    response = requests.get(
        f"https://api.vk.com/method/photos.getWallUploadServer", params=params
    )
    response.raise_for_status()
    response = response.json()
    upload_url = response["response"]["upload_url"]
    return upload_url


def upload_photo(upload_url, image_path, group_id, vk_token):
    with open(image_path, "rb") as file:
        url = upload_url
        files = {
            "file": file, 
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        uploaded_file = response.json()
    if uploaded_file["photo"] != "":
        uploaded_file["group_id"] = group_id
        uploaded_file["access_token"] = vk_token
        uploaded_file["v"] = 5.131
        response_image = requests.post(
            "https://api.vk.com/method/photos.saveWallPhoto", params=uploaded_file
        )
        response_image.raise_for_status()
        saved_image = response_image.json()
        return saved_image["response"]


def publish_post(media_id, owner_id, text, group_id, vk_token):
    group_id = f"-{group_id}"
    attachments = f"photo{owner_id}_{media_id}"
    params = {
        "attachments": attachments,
        "message": text,
        "owner_id": group_id,
        "access_token": vk_token,
        "from_group": 1,
        "v": 5.131,
    }
    response = requests.post("https://api.vk.com/method/wall.post", params=params)
    response.raise_for_status()
    return response.json()


def main():
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    try:
        vk_token = os.environ["VK_TOKEN"]
    except KeyError as e:
        print("Вы не указали VK_TOKEN")
        return

    try:
        vk_group_id = os.environ["VK_GROUP_ID"]
    except KeyError as e:
        print("Вы не указали VK_GROUP_ID")
        return

    try:
        comix = download_random_comix()
    except requests.HTTPError as e:
        print(e)
    image_path = comix["image_path"]

    try:
        upload_url = get_upload_url(vk_token, vk_group_id)
    except requests.HTTPError as e:
        Path.unlink(image_path)
        print(e)
        return

    
    try:
        saved_image = upload_photo(upload_url, image_path, vk_group_id, vk_token)
    except requests.HTTPError as e:
        print(e)
        return
    finally:
        Path.unlink(image_path)

    owner_id = saved_image[0]["owner_id"]
    media_id = saved_image[0]["id"]
    try:
        post = publish_post(media_id, owner_id, comix["text"], vk_group_id, vk_token)
    except requests.HTTPError as e:
        print(e)
        return

    pprint(post)


if __name__ == "__main__":
    main()

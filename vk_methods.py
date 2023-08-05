import os
from os.path import dirname, join
from pprint import pprint

import requests
from dotenv import load_dotenv
from requests import HTTPError


def get_adress_load_image():
    group_id = get_group_id()
    try:
        response = get_request_to_vk(
            "photos.getWallUploadServer", {"group_id": group_id}
        )
        return response["response"]
    except HTTPError as e:
        print("Ошибка соединения")
    except KeyError:
        print("Ошибка запроса")


def get_request_to_vk(method, params={}):
    token = get_access_token()
    params["v"] = 5.131
    params["access_token"] = token
    response = requests.get(f"https://api.vk.com/method/{method}", params=params)
    response.raise_for_status()
    response = response.json()
    return response


def post_request_to_vk(method, params={}):
    token = get_access_token()
    params["v"] = 5.131
    params["access_token"] = token
    response = requests.post(f"https://api.vk.com/method/{method}", params=params)
    response.raise_for_status()
    response = response.json()
    return response["response"]


def get_access_token():
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    try:
        access_token = os.environ["ACCESS_TOKEN"]
    except KeyError as e:
        exit("Вы не заполнили токен")
    return access_token


def get_group_id():
    dotenv_path = join(dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    try:
        group_id = os.environ["GROUP_ID"]
        return group_id
    except KeyError as e:
        exit("Вы не заполнили id группы")


def save_wall_photo(image_path):
    upload_fields = get_adress_load_image()
    with open(image_path, "rb") as file:
        url = upload_fields["upload_url"]
        files = {
            "file": file,  # Вместо ключа "media" скорее всего нужно подставить другое название ключа. Какое конкретно см. в доке API ВК.
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        uploaded_file = response.json()

    if uploaded_file["photo"] != "":
        group_id = get_group_id()
        uploaded_file["group_id"] = group_id
        saved_image = post_request_to_vk("photos.saveWallPhoto", uploaded_file)
        return saved_image


def public_post(saved_image, text):
    media_id = saved_image[0]["id"]
    image_owner_id = saved_image[0]["owner_id"]
    group_id = get_group_id()
    owner_id = f"-{group_id}"
    attachments = f"photo{image_owner_id}_{media_id}"
    params = {"attachments": attachments, "message": text, "owner_id": owner_id}
    response = post_request_to_vk("wall.post", params)

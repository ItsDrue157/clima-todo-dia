import os
import requests


def pegar_chat_id():
    url = f"https://api.telegram.org/bot{os.getenv('token_telegram')}/getUpdates"
    response = requests.get(url).json()
    if response.get("ok"):
        chat_id = response["result"]["id"]
        return str(chat_id)
    else:
        return False
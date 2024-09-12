import json
import time

import requests
import sseclient

from sseclient import SSEClient
from env import settings
from bs4 import BeautifulSoup



class ChatService():

    def __init__(self):
        self.headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}"
        }
        self.urls = {
            settings.CHAT_URL: ["Chat", "GPTs"],
            settings.CHAT_VISION_URL: ["Chat-Vision"],
            settings.CHAT_DOC_LC_URL: ["Chat-Document Long Context"],
            settings.CHAT_DOC_RAG_URL: ["Chat-Document RAG"],
        }

    def get_client(self, mode: str, messages: list, chat_model: dict, store_name: str = "", data_id: str = "") -> SSEClient:
        url = next((url for url, values in self.urls.items() if mode in values), None)
        headers = self.headers
        for message in messages:
            for key in ("search", "plot"):
                message.pop(key, None)

        body = {
            "messages": messages,
            "chat_model": chat_model,
        }
        if store_name:
            body['store_name'] = store_name
        if data_id:
            body['data_id'] = data_id
        # Request
        try:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body,
                                    stream=True,
                                    timeout=30)
            if response.status_code != 200:
                raise Exception(response.content)

            client = sseclient.SSEClient(response)

            return client
        except:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body,
                                    stream=True,
                                    timeout=30)
            if response.status_code != 200:
                raise Exception(response.content)

            client = sseclient.SSEClient(response)

            return client

    # Embed doc
    def embed_docs(self, type: str, urls: list):
        url = settings.CHAT_DOC_EMBED_URL
        headers = {
            "Authorization": f"Bearer {settings.AUTHORIZATION}",
            'accept': 'application/json',
        }

        types_mapping = {
            "Long Context": "lc",
            "RAG": "rag",
        }

        body = {
            "chat_type": types_mapping[type],
            "urls": urls,
        }
        body_json = json.dumps(body)
        files = {
            'request': (None, body_json, 'application/json'),
        }

        session = requests.Session()
        response = session.post(url=url,
                                headers=headers,
                                files=files,
                                timeout=30)
        if response.status_code != 200:
            raise Exception(response.content)

        task_id = response.json()['data']['task_id']

        return self.wait_for_success(task_id)

    # Queue API
    def queue_result(self, task_id: str):
        url = f"{settings.QUEUE_STATUS_URL}/{task_id}"
        headers = self.headers
        response = requests.request(method="get",
                                    url=url,
                                    headers=headers)
        return response.json()

    def wait_for_success(self, task_id: str, interval: int = 2):
        while True:
            result = self.queue_result(task_id)
            status = result["data"]["status"]["task_status"]

            if status == "SUCCESS":
                return result["data"]["task_result"]["data"]["data_id"]

            if status != "STARTED":
                raise ValueError(result["data"]["status"]["task_status"])
            time.sleep(interval)


def get_title(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.title.string if soup.title else 'No title found'
    except requests.exceptions.RequestException as e:
        return url
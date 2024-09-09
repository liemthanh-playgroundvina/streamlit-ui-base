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
            settings.CHAT_DOC_LC_URL: ["ChatDoc-LongContext"],
            settings.CHAT_DOC_RAG_URL: ["ChatDoc-RAG"],
        }

    def get_client(self, mode: str, messages: list, chat_model: dict, store_name: str = "") -> SSEClient:
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


def get_title(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.title.string if soup.title else 'No title found'
    except requests.exceptions.RequestException as e:
        return url
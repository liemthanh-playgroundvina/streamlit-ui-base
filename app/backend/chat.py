import requests
import sseclient
from env import settings
from bs4 import BeautifulSoup



class ChatBotService():
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}"
    }

    model_url_mapper = {
        'AIServices': f'{settings.AI_CENTER_BE_URL}/chat',
    }

    def get_client(self, messages: list, chat_model: dict, store_name: str = ""):
        url = self.model_url_mapper['AIServices']
        headers = self.headers
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


class ChatVisionService():
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}"
    }

    model_url_mapper = {
        'AIServices': f'{settings.AI_CENTER_BE_URL}/chat-vision',
    }

    def get_client(self, messages: list, chat_model: dict):
        url = self.model_url_mapper['AIServices']
        headers = self.headers
        body = {
            "messages": messages,
            "chat_model": chat_model,
        }
        # Request
        try:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body,
                                    stream=True,
                                    timeout=15)
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
                                    timeout=15)
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
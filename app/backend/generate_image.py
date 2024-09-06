import json
import requests
from env import settings


class GenerateImageService():
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}"
    }

    model_url_mapper = {
        'AIServices': f'{settings.AI_CENTER_BE_URL}',
    }

    def gen_prompt_following_style(self, prompt: str, style: str):
        url = self.model_url_mapper['AIServices'] + "/text-to-image/gen-prompt"
        headers = self.headers
        headers["Content-Type"] = "application/json"

        body = {
            "query": prompt,
            "style": style
        }
        # Request
        try:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body)
            if response.status_code != 200:
                raise Exception(response.content)

            style, prompt, negative_prompt = response.json()['data']['style'], response.json()['data']['prompt'], response.json()['data']['negative_prompt']

            return style, prompt, negative_prompt

        except:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body)
            if response.status_code != 200:
                raise Exception(response.content)

            style, prompt, negative_prompt = response.json()['data']['style'], response.json()['data']['prompt'], response.json()['data']['negative_prompt']

            return style, prompt, negative_prompt


    def text_to_image(self, host: str, model_name: str, prompt: str, negative_prompt: str, config: dict):
        url = self.model_url_mapper['AIServices'] + "/text-to-image"
        headers = self.headers
        headers["Content-Type"] = "application/json"

        config["image_content_type"] = "image/png"

        body = {
            "host": host,
            "model_name": model_name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "config": config,
        }
        # Request
        try:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body)
            if response.status_code != 200:
                raise Exception(response.content)

            url = response.json()['data']['file_url']['url']

            return url
        except:
            session = requests.Session()
            response = session.post(url=url,
                                    headers=headers,
                                    json=body)
            if response.status_code != 200:
                raise Exception(response.content)

            url = response.json()['data']['file_url']['url']

            return url


    def image_to_image(self, url_image: str, host: str, model_name: str, prompt: str, negative_prompt: str, config: dict, img_uploader):
        url = self.model_url_mapper['AIServices'] + "/image-to-image"
        headers = self.headers
        headers.pop('Content-Type', None)
        config["image_content_type"] = "image/png"

        body = {
            "url": url_image,
            "host": host,
            "model_name": model_name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "config": config,
        }

        try:
            session = requests.Session()
            if not img_uploader:
                data = {
                    'request': (None, json.dumps(body)),
                }
                response = session.post(url, headers=headers, files=data)
            else:
                files = {'file': (img_uploader.name, img_uploader, img_uploader.type)}
                data = {'request': json.dumps(body)}
                response = requests.post(url, headers=headers, files=files, data=data)

            if response.status_code != 200:
                raise Exception(response.content)

            url = response.json()['data']['file_url']['url']
            return url
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

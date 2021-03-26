import json
from logging import getLogger

import requests
from requests.exceptions import RequestException

class DiscordApi():
    def __init__(self, url, *, logger=None):
        self.logger = logger or getLogger(__name__)
        self.webhook_url = url
        self.user_name = "PayrateChecker"
        self.avatar_url = "https://www.nicehash.com/favicon.ico"

        self.logger.info("discordAPI init, url=%s", url)

    def post_webhook(self, contents):

        json_massage = json.dumps({
            "username": self.user_name,
            "avatar_url": self.avatar_url,
            "content": contents
        })

        try:
            self.logger.debug("post webhook %s", contents)
            response = requests.post(
                self.webhook_url,
                json_massage,
                headers={'Content-Type': 'application/json'},
                timeout=(3.0, 7.5)
            )
            response.raise_for_status()

        except RequestException as err:
            self.logger.warning(err)

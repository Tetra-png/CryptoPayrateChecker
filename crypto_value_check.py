from logging import getLogger

import numpy as np
import requests
from requests.exceptions import RequestException


class CryptoValueChecker():
    def __init__(self, *, logger=None):
        self.logger = logger or getLogger(__name__)
        self.logger.info("CryptoValueChecker init")

    def check_nicehash_paying(self):
        try:
            url = "https://api2.nicehash.com/main/api/v2/public/algo/history?algorithm=DAGGERHASHIMOTO"
            response = requests.get(url, timeout=(3.0, 7.5))
            response.raise_for_status()

            paying_data = np.array(response.json())
            nicehash_6h = np.average(paying_data[-24:, 2]) * 10000

            return nicehash_6h

        except (LookupError, TypeError, RequestException) as err:
            self.logger.warning("nicehash network error: %s", err)
            return -1

    def check_ethermine_paying(self):
        try:
            eth_value = self.check_eth_value()
            btc_value = self.check_btc_value()
            url = "https://api.ethermine.org/miner/008c26f3a2Ca8bdC11e5891e0278c9436B6F5d1E/dashboard/payouts"
            response = requests.get(url, timeout=(3.0, 7.5))
            response.raise_for_status()

            paying_data = response.json()
            average_hashrate = float(paying_data["data"]["estimates"]["averageHashrate"]) / 10 ** 12
            eth_per_day = float(paying_data["data"]["estimates"]["coinsPerMin"]) * 1440
            btc_per_day = (eth_per_day * eth_value) / btc_value
            ethermine_6h = 1 / average_hashrate * btc_per_day

            return ethermine_6h

        except (LookupError, TypeError, RequestException) as err:
            self.logger.warning("ethermine network error: %s", err)
            return -1

    def check_btc_value(self):
        try:
            url = "https://coin.z.com/api/v1/quote/getChart?tv=1&productId=1001&multiBandType=0&bidAskType=1&chartType=1&size=1"
            response = requests.get(url)
            response.raise_for_status()
            chart_data = response.json()

            btc_now = int(chart_data["data"][0]["open"])
            return btc_now

        except (LookupError, TypeError, RequestException) as err:
            self.logger.warning("GMO BTC network error: %s", err)
            return -1

    def check_eth_value(self):
        try:
            url = "https://coin.z.com/api/v1/quote/getChart?tv=1&productId=1002&multiBandType=0&bidAskType=1&chartType=1&size=1"
            response = requests.get(url)
            response.raise_for_status()
            chart_data = response.json()

            eth_now = int(chart_data["data"][0]["open"])
            return eth_now

        except (LookupError, TypeError, RequestException) as err:
            self.logger.warning("GMO ETH network error: %s", err)
            return -1

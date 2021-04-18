import argparse
import json
from logging import getLogger, basicConfig, StreamHandler, FileHandler
import time
import textwrap

from discord_api import DiscordApi
from payrate_checker import PayrateChecker

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug_level", type=int, default=20, help="DEBUG=10, INFO=20(def), WARNING=30")
parser.add_argument("-url1", "--payrate_url", type=str, help="payrate_checkerのほうのdiscord webhook")
parser.add_argument("-url2", "--profit_url", type=str, help="profitのほうのdiscord webhook")
args = parser.parse_args()

# log setting
# 標準出力に出力
sh = StreamHandler()
# ファイル出力
fh = FileHandler("./settings/crypto_payrate_checker.log")

basicConfig(
    level=args.debug_level,
    format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[sh, fh]
    )

logger = getLogger(__name__)

def main():
    with open("./settings/pc_data.json") as f:
        pc_data = json.load(f)

    discord_api_all = DiscordApi(args.payrate_url)
    discord_api = DiscordApi(args.profit_url)
    payrate_checker = PayrateChecker(pc_data)

    while True:
        f = open("./settings/pc_data.json")
        pc_data = json.load(f)
        f.close()

        payrate_checker.pc_data = pc_data

        discord_api_all.post_webhook(payrate_checker.create_now_value())

        # ここから別機能
        contents_list, data_list = payrate_checker.create_profit_list()
        total_power = 0
        total_hashrate = 0
        total_profit_nice = 0
        total_profit_ether = 0

        for profit, data in zip(contents_list, data_list):
            discord_api.post_webhook(profit)
            total_power += data[3]
            total_hashrate += data[4]
            total_profit_nice += data[6]
            total_profit_ether += data[7]

        template = """
            Total \r
            Power: {}W,  HashRate {:.2f}MH/s \r
            Profit(Nicehash):  {}円/day \r
            Profit(Ethermine): {}円/day \r
        """.format(
            total_power, total_hashrate,
            total_profit_nice,
            total_profit_ether
        )
        template = textwrap.dedent(template).strip()
        discord_api.post_webhook("```"+template+"```")
        time.sleep(900)

if __name__ == "__main__":
    main()

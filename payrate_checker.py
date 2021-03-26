import datetime
import textwrap
from logging import getLogger

from crypto_value_check import CryptoValueChecker


class PayrateChecker():
    def __init__(self, pc_data, electric_cost=31, *, logger=None):
        self.logger = logger or getLogger(__name__)
        self.cvc = CryptoValueChecker()

        self.btc_now = self.cvc.check_btc_value()
        self.eth_now = self.cvc.check_eth_value()
        self.nicehash_6h = self.cvc.check_nicehash_paying()
        self.ethermine_6h = self.cvc.check_ethermine_paying()

        self.pc_data = pc_data
        self.electric_cost = electric_cost

        self.logger.info("PayrateChecker init")

    def update_value(self):
        self.btc_now = self.cvc.check_btc_value()
        self.eth_now = self.cvc.check_eth_value()
        self.nicehash_6h = self.cvc.check_nicehash_paying()
        self.ethermine_6h = self.cvc.check_ethermine_paying()

    def create_profit_list(self):
        self.update_value()

        contents_template = """
            Name: {} \r
            devices
            System Power: {}W \r
            PSU Efficiency: {}% 
            {} \r
            Total Power: {}W,  EffectiveHashRate {:.2f}MH/s({:.1f}% rejected) \r
        """
        contents_list = []
        data_list = []

        for pc_name in self.pc_data.keys():
            system_power = int(self.pc_data[pc_name]["System"]["power_consumption"])
            power_efficiency = int(self.pc_data[pc_name]["System"]["power_efficiency"])
            total_power = self._culc_total_power(pc_name)

            rejected_rate = float(self.pc_data[pc_name]["System"]["reject_rate"])
            total_hashrate = self._culc_total_hashrate(pc_name)

            device_contents_list = self._create_device_list(pc_name, total_power, system_power)
            total_power = total_power // (power_efficiency / 100)
            total_hashrate = total_hashrate * ((100 - rejected_rate) / 100)

            profit_nice = int(self.nicehash_6h * total_hashrate * 10**-6 * self.btc_now - (total_power * 24 * self.electric_cost / 1000))
            profit_ether = int(self.ethermine_6h * total_hashrate * 10**-6 * self.btc_now - (total_power * 24 * self.electric_cost / 1000))

            contents = contents_template.format(
                pc_name,
                system_power,
                power_efficiency,
                device_contents_list,
                total_power, total_hashrate, rejected_rate
            )
            contents = textwrap.dedent(contents).strip()
            contents_list.append("```"+contents+"```")
            data_list.append((pc_name, system_power, power_efficiency, total_power, total_hashrate, rejected_rate, profit_nice, profit_ether))

        return contents_list, data_list

    def create_now_value(self):
        self.update_value()

        contents = f"""
            {datetime.datetime.today()} \r
            Prices
            BTC Price(now): {self.btc_now} 円\r
            ETH Price(now): {self.eth_now} 円\r
            \r
            Nicehash paying (6H) \r
            {self.nicehash_6h:.3f} BTC/TH/DAY \r
            \r
            Ethermine paying (6H)\r
            {self.ethermine_6h:.3f} BTC/TH/DAY
        """
        contents = textwrap.dedent(contents).strip()
        contents = "```"+contents+"```"

        return contents

    def _culc_total_power(self, pc_name):
        total_power = int(self.pc_data[pc_name]["System"]["power_consumption"])
        for device_name in self.pc_data[pc_name]["Devices"]:
            power_consumption = int(self.pc_data[pc_name]["Devices"][device_name]["power_consumption"])
            total_power += power_consumption

        return total_power

    def _culc_total_hashrate(self, pc_name):
        total_hashrate = 0
        for device_name in self.pc_data[pc_name]["Devices"]:
            hashrate = float(self.pc_data[pc_name]["Devices"][device_name]["hashrate"])
            fee = float(self.pc_data[pc_name]["Devices"][device_name]["fee"])
            total_hashrate += hashrate * ((100 - fee)/100)

        return total_hashrate

    def _create_device_list(self, pc_name, total_power, system_power):
        device_contents_list = ""
        device_template = """
            {} \r
            Power: {}W,  HashRate {:.2f}MH/s, Fee {:.2f}% \r
            MinHashRate {:.1f}MH/s, {:.0f}% efficient \r
        """
        for device_name in self.pc_data[pc_name]["Devices"]:
            power_consumption = int(self.pc_data[pc_name]["Devices"][device_name]["power_consumption"])
            hashrate = float(self.pc_data[pc_name]["Devices"][device_name]["hashrate"])
            fee = float(self.pc_data[pc_name]["Devices"][device_name]["fee"])

            power_all_ratio = power_consumption + power_consumption / (total_power - system_power) * system_power

            min_nicehash = \
                (power_all_ratio * 24 * self.electric_cost / 1000) / \
                (self.nicehash_6h * 10**-6 * self.btc_now)

            min_ethermine = \
                (power_all_ratio * 24 * self.electric_cost / 1000) / \
                (self.ethermine_6h * 10**-6 * self.btc_now)

            min_hashrate = min_nicehash if min_nicehash >= min_ethermine else min_ethermine
            device_contents_list += device_template.format(
                device_name,
                power_consumption, hashrate, fee,
                min_hashrate, hashrate / min_hashrate * 100
            )

        return device_contents_list

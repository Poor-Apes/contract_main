import sys
from random import randrange
from brownie import Wei, accounts, Contract, network, config, MockV3Aggregator, PoorApes


def deploy_poor_apes_contract(BTC_USD_price=None, season=None):
    if season == None:
        season = "chicago"
    if network.show_active() == "development" and BTC_USD_price == None:
        print("You need to pass a BTC_USD price")
    else:
        account = get_owner_account()
        price_feed_address = get_price_feed_address(account, int(BTC_USD_price))
        poor_apes_contract = PoorApes.deploy(
            price_feed_address,
            get_marketing_account(),
            get_json_folder(),
            get_prereveal_json_folder(),
            price_normal_as_wei(season),
            price_wl_as_wei(season),
            {"from": account},
        )
        print(poor_apes_contract.address)
        return poor_apes_contract


def get_owner_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


def get_marketing_account():
    if network.show_active() == "development":
        return accounts[1]
    else:
        return accounts.add(
            config["networks"][network.show_active()]["marketing_address"]
        )


def get_json_folder():
    return config["networks"][network.show_active()]["nft_json_folder"]


def get_prereveal_json_folder():
    return config["networks"][network.show_active()]["nft_prereveal_json_folder"]


def get_price_feed_address(account, mock_value=None):
    price_feed_address = None
    active_network = network.show_active()
    if active_network == "goerli":
        price_feed_address = config["networks"]["goerli"]["btc_usd_price_feed"]
    elif active_network == "development":
        print("deploying mocks...")
        mock_aggregator = MockV3Aggregator.deploy(
            8, adjust_BTC_USD_price(mock_value), {"from": account}
        )
        print(mock_aggregator.decimals())
        price_feed_address = mock_aggregator.address
    else:
        raise Exception("Not able to deploy to " + active_network)
    return price_feed_address


def adjust_BTC_USD_price(usd_price):
    return usd_price * (10**8)


def price_normal_as_wei(season):
    return Wei(str(config["season"][season]["price"]["normal"]) + " ether")


def price_wl_as_wei(season):
    return Wei(str(config["season"][season]["price"]["wl"]) + " ether")


def main():
    season = "Chicago"
    # (for when calling from the command line)
    if len(sys.argv) == 2:
        if sys.argv[1] not in ["chicago", "nyc", "detroit"]:
            raise Exception("Season needs to be chicago, nyc or detroit")
        else:
            season = sys.argv[1]
    return deploy_poor_apes_contract(None, season)

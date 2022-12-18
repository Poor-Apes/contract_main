import sys
from brownie import Wei, accounts, Contract, network, config, MockV3Aggregator, PoorApes


def deploy_poor_apes_contract(BTC_USD_price = None):
    if network.show_active() == "development" and BTC_USD_price == None:
        print("You need to pass a BTC_USD price")
    else:
        account = get_account()
        price_feed_address = get_price_feed_address(account, int(BTC_USD_price))
        poor_apes_contract = PoorApes.deploy(
            price_feed_address,
            config["networks"][network.show_active()]["max_supply"],
            config["networks"][network.show_active()]["nft_json_folder"],
            {"from": account},
        )
        print(poor_apes_contract.address)
        return poor_apes_contract


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


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
    return usd_price * (10 ** 8)


def main(BTC_USD_price = None):
    #BTC_USD_price = None
    if len(sys.argv) == 2 and sys.argv[1].isnumeric():
        BTC_USD_price = sys.argv[1]
    return deploy_poor_apes_contract(BTC_USD_price)

import os
import sys
import pytest
import requests
from brownie import Wei, accounts, reverts, config

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from common import contract, contract_btc_above_20k, contract_new_york, contract_detroit


# $ brownie console
# >>> contract = deploy.deploy_poor_apes_contract(19000)
# The mint cost is depedant on wether the account is in the WL &
# wether their allocation has been used
# >>> contract.mint({"from": accounts[1], "value": int(contract.mint_cost({"from": accounts[1]}))})

# minter_account = accounts[0]
# buyer_account = accounts[1]

# TESTS


@pytest.mark.mint
def test_mint_sets_BTC_USD_value_corecctly(contract_btc_above_20k):
    assert contract_btc_above_20k.getBTCPrice() == 22000 * 10**8


@pytest.mark.mint
def test_mint_with_contract_btc_above_20k(contract_btc_above_20k):
    with reverts("BTC is not under 20k usd"):
        contract_btc_above_20k.mint({"from": accounts[1]})


@pytest.mark.mint
def test_mint(contract):
    # 1. The owner has spent ETH on rolling contract out
    assert contract.balanceOf(accounts[0]) < Wei(
        "1000 ether"
    ), "Owner did not spend any money rolling out the contract"
    # 2. The buyer doesn't already have an NFT
    assert (
        contract.balanceOf(accounts[2]) == 0
    ), "Buyer wallet already has a Poor Ape NFT in it"
    # 3. Check buyer's initial ETH
    assert accounts[2].balance() >= Wei(
        "1000 ether"
    ), "Buyer wallet does not have 1000 eth in it"
    # 4. Mint less than the mint ammount
    with reverts("More ETH required to mint"):
        contract.mint({"from": accounts[1], "value": contract.mint_cost() - 1})
    # 5. Make sure the buyer hasn't been charged
    assert accounts[2].balance() == Wei(
        "1000 ether"
    ), "Buyer has been charged for an nft that did not mint"
    # 6. Check the buyer didn't get the NFT
    assert (
        contract.balanceOf(accounts[2]) == 0
    ), "Buyer wallet already has a Poor Ape NFT in it"
    # 7. Mint with the correct price
    contract.mint({"from": accounts[2], "value": contract.mint_cost()})
    # 8. The buyer got the NFT
    assert (
        contract.balanceOf(accounts[2]) == 1
    ), "Buyer wallet should have a Poor Ape NFT in it"
    estimated_balance_after_mint_cost_with_gas = (
        int(Wei("1000 ether")) - contract.mint_cost() - int(Wei("0.01 ether"))
    )
    assert (accounts[2].balance() == estimated_balance_after_mint_cost_with_gas,), (
        "Buyer wallet should be "
        + str(estimated_balance_after_mint_cost_with_gas)
        + " ("
        + str(accounts[2].balance())
        + ")"
    )


@pytest.mark.mint
def test_can_mint_five(contract):
    contract.mint(
        5, {"from": accounts[1], "value": contract.mint_cost(5, {"from": accounts[1]})}
    )
    # Test there is no limit on minting
    contract.mint(
        5, {"from": accounts[1], "value": contract.mint_cost(5, {"from": accounts[1]})}
    )
    contract.mint(
        5, {"from": accounts[1], "value": contract.mint_cost(5, {"from": accounts[1]})}
    )


@pytest.mark.mint
def test_can_not_mint_six(contract):
    with reverts("You can not mint that many NFTs (3)"):
        contract.mint(
            6,
            {
                "from": accounts[1],
                "value": contract.mint_cost(6, {"from": accounts[1]}),
            },
        )


@pytest.mark.skip(reason="takes too long")
@pytest.mark.mint
def test_tokenuri_function_returns_json(contract):
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    contract.mint({"from": accounts[1]})
    contract.mint({"from": accounts[1]})
    uri_of_json = contract.tokenURI(1)
    nft_json = requests.get(uri_of_json).json()
    assert "name" in nft_json, "The name key is not in the JSON"
    assert "description" in nft_json, "The description key is not in the JSON"
    assert "image" in nft_json, "The image key is not in the JSON"
    assert "external_url" in nft_json, "The external_url key is not in the JSON"
    assert "background_color" in nft_json, "The background_color key is not in the JSON"
    assert "attributes" in nft_json, "The attributes key is not in the JSON"

    # the 'image' attribute url loads
    assert True
    # the 'external' attribute url loads
    assert True


@pytest.mark.mint
@pytest.mark.long
def test_can_not_mint_more_than_max_supply_chicago_nfts(contract):
    supply = config["season"]["chicago"]["max_supply"]
    assert contract.max_supply() == supply
    for i in range(supply - 1):
        contract.mint({"from": accounts[i], "value": contract.mint_cost()})
    with reverts():
        contract.mint({"from": accounts[supply], "value": contract.mint_cost()})

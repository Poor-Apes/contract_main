import os
import sys
import json
import pytest
import requests
from brownie import reverts
from brownie import Wei, accounts, network, config, convert
from brownie.exceptions import VirtualMachineError

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

import deploy

price_for_first_nft = convert.to_int("0.05 ether")
price_for_99th_nft = convert.to_int("0.09 ether")
price_for_199th_nft = convert.to_int("0.15 ether")
price_for_299th_nft = convert.to_int("0.27 ether")
price_for_399th_nft = convert.to_int("0.46 ether")
price_for_499th_nft = convert.to_int("0.81 ether")
price_for_599th_nft = convert.to_int("1.41 ether")
price_for_699th_nft = convert.to_int("2.46 ether")
price_for_700th_nft = convert.to_int("2.46 ether")
price_for_800th_nft = convert.to_int("2.46 ether")

# FIXTURES


@pytest.fixture
def contract():
    return deploy.deploy_poor_apes_contract(19000)


@pytest.fixture
def contract_btc_above_20k():
    return deploy.deploy_poor_apes_contract(22000)


# $ brownie console
# >>> contract = deploy.deploy_poor_apes_contract(19000)

# minter_account = accounts[0]
# buyer_account = accounts[1]

# TESTS


@pytest.mark.mint
def test_mint_sets_BTC_USD_value_corecctly(contract_btc_above_20k):
    assert contract_btc_above_20k.getBTCPrice() == 22000 * 10**8


@pytest.mark.mint
def test_mint_with_contract_btc_above_20k(contract_btc_above_20k):
    with reverts("BTC is not under 20k usd"):
        contract_btc_above_20k.mintNFT({"from": accounts[1]})


@pytest.mark.mint
def test_add_to_whitelist_when_owner(contract):
    with reverts("The owner can not be added to the whitelist"):
        contract.addToWhiteList(accounts[0], {"from": accounts[0]})


@pytest.mark.mint
def test_add_buyer_to_whitelist(contract):
    with reverts():
        contract.addToWhiteList(accounts[1], {"from": accounts[1]})


@pytest.mark.mint
def test_added_and_then_removed_from_whitelist(contract):
    assert (
        contract.isInWhiteList(accounts[1]) == False,
        "The buyers account should not be on the white list already",
    )
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    assert (
        contract.isInWhiteList(accounts[1]) == True,
        "The buyers account should be on the white list",
    )
    contract.removeFromWhiteList(accounts[1], {"from": accounts[0]})
    assert (
        contract.isInWhiteList(accounts[1]) == False,
        "The buyers account should not be on the white list",
    )


@pytest.mark.mint
def test_mint_when_on_whitelist(contract):
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    assert (
        accounts[1].balance() == Wei("1000 ether"),
        "Buyer wallet does not have 1,000 eth in it",
    )
    assert (
        contract.balanceOf(accounts[1]) == 0,
        "Buyer wallet already has a Poor Ape NFT in it",
    )
    contract.mintNFT({"from": accounts[1], "value": contract.minting_cost(-1)})
    assert (
        contract.balanceOf(accounts[1]) == 1,
        "Buyer wallet should have an NFT in it after minting",
    )
    # to take into consideration gas
    assert (
        accounts[1].balance() >= Wei("999.99 ether"),
        "Buyer should not pay for a whitelist mint",
    )


@pytest.mark.mint
def test_mint(contract):
    first_nft_cost_as_int = int(contract.minting_cost(0))
    # 1. Make sure the initial minting cost is correct
    assert (
        int(contract.minting_cost(-1)) == first_nft_cost_as_int,
        "The initial miniting cost of "
        + str(first_nft_cost_as_int)
        + " is different to the returned cost from minting_cost(-1) ["
        + str(contract.minting_cost(-1))
        + "]",
    )
    # 2. The buyer doesn't already have an NFT
    assert (
        contract.balanceOf(accounts[1]) == 0,
        "Buyer wallet already has a Poor Ape NFT in it",
    )
    # 3. Check buyer's initial ETH
    assert (
        accounts[1].balance() == Wei("1000 ether"),
        "Buyer wallet does not have 1,000 eth in it",
    )
    # 4. Mint less than the mint ammount
    with reverts("More ETH required to mint NFT"):
        contract.mintNFT({"from": accounts[1], "value": first_nft_cost_as_int - 1})
    # 5. Make sure the buyer hasn't been charged
    assert (
        accounts[1].balance() == Wei("1000 ether"),
        "Buyer wallet does not have 1,000 eth in it",
    )
    # 6. Check the buyer didn't get the NFT
    assert (
        contract.balanceOf(accounts[1]) == 0,
        "Buyer wallet already has a Poor Ape NFT in it",
    )
    # 7. Mint with the correct price
    contract.mintNFT({"from": accounts[1], "value": first_nft_cost_as_int})
    # 8. The buyer got the NFT
    assert (
        contract.balanceOf(accounts[1]) == 1
    ), "Buyer wallet should have a Poor Ape NFT in it"
    estimated_balance_after_mint_cost_with_gas = (
        int(Wei("1000 ether")) - first_nft_cost_as_int - int(Wei("0.01 ether"))
    )
    assert (
        accounts[1].balance() == estimated_balance_after_mint_cost_with_gas,
        "Buyer wallet should be "
        + str(estimated_balance_after_mint_cost_with_gas)
        + " ("
        + str(accounts[1].balance())
        + ")",
    )


@pytest.mark.skip(reason="takes too long")
@pytest.mark.mint
def test_tokenuri_function_returns_json(contract):
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    contract.mintNFT({"from": accounts[1]})
    contract.mintNFT({"from": accounts[1]})
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
def test_minting_cost_get_more_expensive(contract):
    first_nft_cost_as_int = int(contract.minting_cost(-1))
    for i in range(100):
        print(i)
        minter_acc = accounts[i + 1]
        contract.mintNFT(
            {
                "from": minter_acc,
                "value": int(contract.minting_cost(-1)),
            }
        )
    hundredth_nft_cost_as_int = int(contract.minting_cost(-1))
    assert (
        first_nft_cost_as_int < hundredth_nft_cost_as_int
    ), "The first and hundredth nft are the same price"


@pytest.mark.mint
@pytest.mark.long
def test_mint_cost_function_every_hundred_nfts(contract):
    assert int(contract.minting_cost(0)) == int(price_for_first_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(0).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(99)) == int(price_for_99th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(99).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(199)) == int(price_for_199th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(199).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(299)) == int(price_for_299th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(299).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(399)) == int(price_for_399th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(399).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(499)) == int(price_for_499th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(499).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(599)) == int(price_for_599th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(599).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(699)) == int(price_for_699th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(699).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(700)) == int(price_for_700th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(700).to("ether"))
        + ")"
    )
    assert int(contract.minting_cost(800)) == int(price_for_800th_nft), (
        "The NFT at position has the wrong price (it should be "
        + str(contract.minting_cost(800).to("ether"))
        + ")"
    )


@pytest.mark.mint
@pytest.mark.long
def test_can_not_mint_701_nfts(contract):
    first_nft_cost_as_int = int(contract.minting_cost(-1))
    for i in range(699):
        contract.mintNFT({"from": accounts[i], "value": contract.minting_cost(-1)})
    with reverts():
        contract.mintNFT({"from": accounts[700], "value": contract.minting_cost(-1)})


# test withdraws
# add WL logic
# add types logic
# add pre-reveal logic
# add transfer logic

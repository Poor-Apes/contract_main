import os
import sys
import pytest
import requests
from brownie import reverts
from brownie import Wei, accounts

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from common import contract


@pytest.mark.whitelist
def test_add_to_whitelist_when_owner(contract):
    with reverts("The owner can not be added to the whitelist"):
        contract.addToWhiteList(accounts[0], {"from": accounts[0]})


@pytest.mark.whitelist
def test_add_buyer_to_whitelist(contract):
    with reverts():
        contract.addToWhiteList(accounts[1], {"from": accounts[1]})


@pytest.mark.whitelist
def test_added_and_then_removed_from_whitelist(contract):
    assert (
        contract.isInWhiteList(accounts[1]) == False
    ), "The buyers account should not be on the white list already"
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    assert (
        contract.isInWhiteList(accounts[1]) == True
    ), "The buyers account should be on the white list"
    contract.removeFromWhiteList(accounts[1], {"from": accounts[0]})
    assert (
        contract.isInWhiteList(accounts[1]) == False
    ), "The buyers account should not be on the white list"


# NOTE: This needs to be re-done
@pytest.mark.mint
def test_mint_when_on_whitelist(contract):
    original_cost = contract.mint_cost({"from": accounts[3]})
    contract.addToWhiteList(accounts[3], {"from": accounts[0]})
    assert original_cost != contract.mint_cost(
        {"from": accounts[3]}
    ), "Adding the account to the whitelist did not make a difference to the mint price"
    assert accounts[3].balance() == Wei(
        "1000 ether"
    ), "Buyer wallet does not have 1,000 eth in it"
    assert (
        contract.balanceOf(accounts[3]) == 0
    ), "Buyer wallet should not have a Poor Ape NFT in it"
    contract.mint(
        {"from": accounts[3], "value": contract.mint_cost({"from": accounts[3]})}
    )
    assert (
        contract.balanceOf(accounts[3]) == 1
    ), "Buyer wallet should have an NFT in it after minting"
    # to take into consideration gas
    assert accounts[3].balance() >= Wei("1000 ether") - contract.mint_price_whitlist(
        {"from": accounts[3]}
    ), "Buyer should pay whitelist prices"


@pytest.mark.whitelist
def test_minting_and_minting_on_wl_are_different_cost(contract):
    contract.addToWhiteList(accounts[3], {"from": accounts[0]})
    assert contract.mint_cost(1, {"from": accounts[3]}) != contract.mint_cost(
        1, {"from": accounts[4]}
    ), "Minting from account 1 is the same cost as minting from acount 2 even though account 2 is on the whitelist"
    # Test that they actully have different minting costs
    account_1_balance = accounts[3].balance()
    account_2_balance = accounts[4].balance()
    contract.mint(
        1,
        {
            "from": accounts[3],
            "value": contract.mint_cost(1, {"from": accounts[3]}),
        },
    )
    contract.mint(
        1,
        {
            "from": accounts[4],
            "value": contract.mint_cost(1, {"from": accounts[4]}),
        },
    )
    assert (account_1_balance - accounts[3].balance()) != (
        account_2_balance - accounts[4].balance()
    ), "Even though account 3 is on the whitelist the minting costs of account 3 & 4 are the same"


@pytest.mark.whitelist
def test_being_on_the_wl_only_works_for_two_mints(contract):
    mint_price = contract.mint_cost(2, {"from": accounts[1]})
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    wl_mint_price = contract.mint_cost(2, {"from": accounts[1]})
    # Can not mint 3 NFTs when on WL
    with reverts("You can not mint that many NFTs (1)"):
        contract.mint(3, {"from": accounts[1], "value": wl_mint_price})
    # Mint 2 NFTs
    contract.mint(2, {"from": accounts[1], "value": wl_mint_price})
    # Can not mint another 2 NFTs for WL prices
    with reverts("More ETH required to mint"):
        contract.mint(2, {"from": accounts[1], "value": wl_mint_price})
    # But can mint for normal prices
    contract.mint(2, {"from": accounts[1], "value": mint_price})
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    contract.removeFromWhiteList(accounts[1], {"from": accounts[0]})
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    # Can not mint another 2 NFTs for WL prices
    with reverts("More ETH required to mint"):
        contract.mint(2, {"from": accounts[1], "value": wl_mint_price})
    # But can mint for normal prices
    contract.mint(2, {"from": accounts[1], "value": mint_price})

import os
import sys
import json
import pytest
from brownie import Wei, accounts, network, config, MockV3Aggregator, PoorApes
from brownie.exceptions import VirtualMachineError

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

import deploy

# $ brownie console
# >>> contract = deploy.deploy_poor_apes_contract(19000)

# minter_account = accounts[0]
# buyer_account = accounts[1]

first_nft_cost = "0.16 ether"


def test_mint_sets_BTC_USD_value_corecctly():
    contract = deploy.deploy_poor_apes_contract(22000)
    assert contract.getBTCPrice() == 22000 * 10 ** 8

def test_mint_with_btc_above_20k():
    contract = deploy.deploy_poor_apes_contract(22000)
    with pytest.reverts("BTC is not under 20k usd"):
        tx = contract.mintNFT({"from": accounts[1]})

def test_mint_when_not_on_whitelist():
    contract = deploy.deploy_poor_apes_contract(19000)
    with pytest.reverts("You are not in the whitelist"):
        contract.mintNFT({"from": accounts[1]})

def test_add_to_whitelist_when_owner():
    contract = deploy.deploy_poor_apes_contract(19000)
    with pytest.reverts("The owner can not be added to the whitelist"):
        contract.addToWhiteList(accounts[0], {"from": accounts[0]})

def test_add_buyer_to_whitelist():
    contract = deploy.deploy_poor_apes_contract(19000)
    with pytest.reverts():
        contract.addToWhiteList(accounts[1], {"from": accounts[1]})

def test_mint_when_added_and_then_removed_from_whitelist():
    contract = deploy.deploy_poor_apes_contract(19000)
    assert(contract.isInWhiteList(accounts[1]) == False, "The buyers account should not be on the white list already")
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    assert(contract.isInWhiteList(accounts[1]) == True, "The buyers account should be on the white list")
    contract.removeFromWhiteList(accounts[1], {"from": accounts[0]})
    assert(contract.isInWhiteList(accounts[1]) == False, "The buyers account should not be on the white list")
    with pytest.reverts("You are not in the whitelist"):
        contract.mintNFT({"from": accounts[1]})

def test_mint_when_on_whitelist():
    contract = deploy.deploy_poor_apes_contract(19000)
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    assert(accounts[1].balance() == Wei("1000 ether"), "Buyer wallet does not have 1,000 eth in it")
    assert(contract.balanceOf(accounts[1]) == 0, "Buyer wallet already has a Poor Ape NFT in it")
    contract.mintNFT({"from": accounts[1]})
    assert(contract.balanceOf(accounts[1]) == 1, "Buyer wallet should have an NFT in it after minting")
    # to take into consideration gas
    assert(accounts[1].balance() >= Wei("999.99 ether"), "Buyer should not pay for a whitelist mint")

def test_mint():
    contract = deploy.deploy_poor_apes_contract(19000)
    # 1. Disable presale
    contract.setPresale(0);
    first_nft_cost_as_int = int(Wei(first_nft_cost))
    # 2. Make sure the initial minting cost is correct
    assert(int(contract.minting_cost(-1)) == first_nft_cost_as_int, "The initial miniting cost of "+str(first_nft_cost_as_int)+" is different to the returned cost from minting_cost(-1) ["+str(contract.minting_cost(-1))+"]")
    # 3. The buyer doesn't already have an NFT
    assert(contract.balanceOf(accounts[1]) == 0, "Buyer wallet already has a Poor Ape NFT in it")
    # 4. Check buyer's initial ETH
    assert(accounts[1].balance() == Wei("1000 ether"), "Buyer wallet does not have 1,000 eth in it")
    # 5. Mint less than the mint ammount
    with pytest.reverts("More ETH required to mint NFT"):
        contract.mintNFT({"from": accounts[1], "value": first_nft_cost_as_int - 1})
    # 6. Make sure the buyer hasn't been charged
    assert(accounts[1].balance() == Wei("1000 ether"), "Buyer wallet does not have 1,000 eth in it")
    # 7. Check the buyer didn't get the` NFT
    assert(contract.balanceOf(accounts[1]) == 0, "Buyer wallet already has a Poor Ape NFT in it")
    # 8. Mint with the correct price
    contract.mintNFT({"from": accounts[1], "value": first_nft_cost_as_int})
    # 9. The buyer got the NFT
    assert(contract.balanceOf(accounts[1]) == 1, "Buyer wallet should have a Poor Ape NFT in it")
    estimated_balance_after_mint_cost_with_gas = int(Wei("1000 ether")) - first_nft_cost_as_int - int(Wei("0.01 ether"))
    assert(accounts[1].balance() == estimated_balance_after_mint_cost_with_gas, "Buyer wallet should be "+str(estimated_balance_after_mint_cost_with_gas)+" ("+str(accounts[1].balance())+")")

def test_tokenuri_function_returns_json():
    contract = deploy.deploy_poor_apes_contract(19000)
    contract.addToWhiteList(accounts[1], {"from": accounts[0]})
    contract.mintNFT({"from": accounts[1]})
    nft_json_as_text = contract.tokenURI(0)
    nft_json = json.load(nft_json_as_text)
    assert("name" in nft_json, "The name key is not in the JSON")
    assert("description" in nft_json, "The description key is not in the JSON")
    assert("image" in nft_json, "The image key is not in the JSON")
    assert("external_url" in nft_json, "The external_url key is not in the JSON")
    assert("background_color" in nft_json, "The background_color key is not in the JSON")
    assert("attributes" in nft_json, "The attributes key is not in the JSON")

    # the 'image' attribute url loads
    assert True
    # the 'external' attribute url loads
    assert True

def test_max_mint_for_account():
    # uint256 public maxMintAmount = 3;
    assert True

def test_minting_cost_get_more_expensive():
    assert True

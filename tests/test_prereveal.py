import os
import sys
import pytest
import requests
from brownie import reverts
from brownie import Wei, accounts

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from deploy import get_prereveal_json_folder, get_json_folder
from common import contract


@pytest.mark.prereveal
def test_prereveal_set_to_true(contract):
    assert (
        contract.prereveal() == True
    ), "prereveal is not set to true when the contract is instantiated"
    contract.disablePrereveal({"from": accounts[0]})
    # This function should not exist
    try:
        contract.enablePrereveal({"from": accounts[0]})
        assert False
    except AttributeError:
        assert True
    # You should not be able to see the IPFS_JSON_Folder hash
    try:
        contract.IPFS_JSON_Folder()
        assert False
    except AttributeError:
        assert True
    # You should be able to see the IPFS_JSON_Folder hash
    try:
        contract.IPFS_prereveal_JSON_Folder()
        assert True
    except AttributeError:
        assert False
    assert (
        contract.prereveal() == False
    ), "prereveal is not set to false after disablePrereveal() is run"


@pytest.mark.prereveal
def test_prereveal_URI(contract):
    # Have to create an NFT before you can get the URI
    contract.mint(
        {"from": accounts[1], "value": int(contract.mint_cost({"from": accounts[1]}))}
    )
    assert get_prereveal_json_folder() in contract.tokenURI(
        0
    ), "prereveal json folder hash not found in URI"
    # we should have a different URI when prereveal is disabled
    contract.disablePrereveal({"from": accounts[0]})
    # assert True == False
    assert get_json_folder() in contract.tokenURI(
        0
    ), "json folder hash not found in URI"

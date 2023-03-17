import os
import sys
import pytest
from brownie import Wei, accounts, network, config, convert, reverts

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from common import contract


@pytest.mark.withdraw
def test_mint_and_then_withdraw(contract):
    for x in range(10):
        contract.mint({"from": accounts[1], "value": int(contract.mint_cost(-1))})
    # The deployers wallet balance BEFORE withdraw
    assert (
        accounts[0].balance() < Wei("1000 ether"),
        "Creators wallet should have a balance of greater than 999.99 ETH",
    )
    contract.withdraw({"from": accounts[0]})
    assert (
        accounts[0].balance() > Wei("1000 ether"),
        "Creators wallet should have a balance of greater than 1000 ETH after withdrawing",
    )

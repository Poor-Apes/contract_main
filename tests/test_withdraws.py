import os
import sys
import pytest
from brownie import Wei, accounts, network, config, convert, reverts

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from common import contract


@pytest.mark.withdraw
@pytest.mark.long
def test_owner_withdraw(contract):
    # Can't withdraw at the begining of the mint
    with reverts("Mint has not finished"):
        contract.withdraw_owner({"from": accounts[0]})
    for x in range(698):
        contract.mint({"from": accounts[x], "value": int(contract.mint_cost())})
    # Can't withdraw before the mint has finished
    with reverts("Mint has not finished"):
        contract.withdraw_owner({"from": accounts[0]})
    contract.mint({"from": accounts[699], "value": int(contract.mint_cost())})
    # Marketing needs to withdraw before the Owner
    with reverts("Marketing needs to withdraw first"):
        contract.withdraw_owner({"from": accounts[0]})


@pytest.mark.withdraw
@pytest.mark.long
def test_marketing_withdraw(contract):
    # The owner can't withdraw from the withdraw_marketing function
    with reverts("Only marketing can call this function"):
        contract.withdraw_marketing({"from": accounts[0]})
    # Even if marketing calls the withdraw_marketing function the mint has to finish
    with reverts("Mint has to finish"):
        contract.withdraw_marketing({"from": accounts[1]})
    for x in range(698):
        contract.mint({"from": accounts[x], "value": int(contract.mint_cost())})
    # One more NFT has to be minted before marketing can call withdraw_marketing
    with reverts("Mint has to finish"):
        contract.withdraw_marketing({"from": accounts[1]})
    contract.mint({"from": accounts[699], "value": int(contract.mint_cost())})
    # Owner still can't call widraw_marketing
    with reverts("Only marketing can call this function"):
        contract.withdraw_marketing({"from": accounts[0]})
    marketing_balance = accounts[1].balance()
    # Withdraw_marketing should work
    contract.withdraw_marketing({"from": accounts[1]})
    # Marketing
    assert (
        accounts[1].balance() == marketing_balance + contract.marketing_budget_in_ETH(),
        "The market account does not have the funds after the withdraw",
    )


@pytest.mark.withdraw
@pytest.mark.long
def test_marketing_withdrawing_twice(contract):
    for x in range(699):
        print(x)
        contract.mint({"from": accounts[x], "value": int(contract.mint_cost())})
    contract.withdraw_marketing({"from": accounts[1]})
    marketing_balance = accounts[1].balance()
    with reverts("Marketing has already withdrawn"):
        contract.withdraw_marketing({"from": accounts[1]})
    # And the funds in the marketing address shouldn't have changed
    assert (
        accounts[1].balance() == marketing_balance + contract.marketing_budget_in_ETH(),
        "Marketing did not recieve the funds after calling withdraw_marketing()",
    )


@pytest.mark.withdraw
@pytest.mark.long
def test_marketing_withdraw_and_then_owner_withdraw(contract):
    owner_balance = accounts[0].balance()
    for x in range(699):
        print(x)
        contract.mint({"from": accounts[x], "value": int(contract.mint_cost())})
    # Just double checking
    with reverts("Marketing needs to withdraw first"):
        contract.withdraw_owner({"from": accounts[0]})
    # Marketing then ...
    contract.withdraw_marketing({"from": accounts[1]})
    # ... the Owner
    contract_balance = contract.balance()
    assert (
        owner_balance == accounts[0].balance(),
        "The owner recieved eth after marketing withdrew. This should not happen!",
    )
    # Now the owner can withdraw
    contract.withdraw_owner({"from": accounts[0]})
    assert (
        owner_balance == accounts[0].balance() + contract_balance,
        "The owner did not recieve the funds after calling withdraw_owner()",
    )

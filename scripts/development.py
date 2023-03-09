import sys
from brownie import Wei, accounts


def create_more_accounts(num_acc: int):
    if num_acc > 49:
        raise ValueError("Cant create that many accounts")
    for x in range(num_acc):
        accounts.add()
        acc = accounts[10 + x]
        accounts[0].transfer(acc, "2 ether")

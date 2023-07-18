import os
import sys
import pytest
from brownie import accounts, reverts, FreeMint

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from deploy import deploy_poor_apes_contract


def mint_all_three_contracts():
    accessories = FreeMint.deploy({"from": accounts[0]})
    accommodation = FreeMint.deploy({"from": accounts[0]})
    contract = deploy_poor_apes_contract(19000, "chicago", accessories, accommodation)
    return [contract, accessories, accommodation]


@pytest.mark.whitelist_free_mints
def test_own_both_free_mints_Minting_accessoires_first():
    account = accounts[5]
    contract, accessories, accommodation = mint_all_three_contracts()
    assert contract.ownsBothFreeMints(account) == False, (
        "account "
        + str(account)
        + " has both free mints even though nothing has been minted yet"
    )
    accessories.mint({"from": account})
    assert contract.ownsBothFreeMints(account) == False, (
        "account " + str(account) + " only has the accessories mint, not both mints"
    )
    accommodation.mint({"from": account})
    assert contract.ownsBothFreeMints(account) == True, (
        "account " + str(account) + " has both mint"
    )


@pytest.mark.whitelist_free_mints
def test_own_both_free_mints_Minting_accommodation_first():
    account = accounts[6]
    contract, accessories, accommodation = mint_all_three_contracts()
    assert contract.ownsBothFreeMints(account) == False, (
        "account "
        + str(account)
        + " has both free mints even though nothing has been minted yet"
    )
    accommodation.mint({"from": account})
    assert contract.ownsBothFreeMints(account) == False, (
        "account " + str(account) + " only has the accommodation mint, not both mints"
    )
    accessories.mint({"from": account})
    assert contract.ownsBothFreeMints(account) == True, (
        "account " + str(account) + " has both mints and should return true"
    )


@pytest.mark.whitelist_free_mints
def test_free_mint_wl_has_precedence_over_normal_wl():
    account = accounts[7]
    contract, accessories, accommodation = mint_all_three_contracts()
    accommodation.mint({"from": account})
    accessories.mint({"from": account})
    contract.addToWhiteList(account, {"from": accounts[0]})
    num_nfts = 2
    mint_cost = contract.mint_cost(num_nfts, {"from": account})
    two_free_mints_mint_cost = contract.mint_price_both_free_mints() * 2
    assert (
        mint_cost == two_free_mints_mint_cost
    ), "The mint price should be the two-free-mints mint price"
    contract.mint(
        num_nfts,
        {
            "from": account,
            "value": two_free_mints_mint_cost * num_nfts,
        },
    )


@pytest.mark.whitelist_free_mints
def test_minting_when_account_has_both_free_mints():
    account = accounts[8]
    contract, accessories, accommodation = mint_all_three_contracts()
    accommodation.mint({"from": account})
    accessories.mint({"from": account})
    # 1. Check can't mint more then two
    allowed_num_nfts = 2
    too_many_nfts = 3
    with reverts("You can not mint that many NFTs (2)"):
        contract.mint(
            too_many_nfts,
            {
                "from": account,
                "value": contract.mint_cost(too_many_nfts, {"from": account}),
            },
        )
    # 2. Mint price is different from standard price
    normal_account_mint_cost = contract.mint_cost({"from": accounts[9]})
    assert (
        normal_account_mint_cost != 0
    ), "The mint cost for people who have both free mints is wrong"
    # 3. Mint normally
    contract.mint(
        allowed_num_nfts,
        {
            "from": account,
            "value": 0,
        },
    )
    # 4. Can't mint again for the same price
    with reverts("More ETH required to mint"):
        contract.mint(
            allowed_num_nfts,
            {
                "from": account,
                "value": 0,
            },
        )
    # 5. Can't mint for the WL price
    contract.addToWhiteList(account, {"from": accounts[0]})
    with reverts("More ETH required to mint"):
        contract.mint(
            allowed_num_nfts,
            {
                "from": account,
                "value": contract.mint_price_whitlist(),
            },
        )
    # 6. Can mint for the normal price
    normal_cost = contract.mint_cost(allowed_num_nfts, {"from": account})
    assert normal_cost != 0, "After minting the mint price should be the normal price"
    contract.mint(
        allowed_num_nfts,
        {
            "from": account,
            "value": normal_cost,
        },
    )

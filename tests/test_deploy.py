import os
import sys
import pytest

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

from common import contract
from deploy import deploy_poor_apes_contract


@pytest.mark.deploy
def test_default_season_for_deploy_is_chicago(contract):
    default_season = "Chicago"
    assert default_season in contract.name(), (
        "The default season is not " + default_season
    )


@pytest.mark.deploy
def test_cant_use_string_as_BTC_USD_price():
    try:
        deploy_poor_apes_contract("this is a string")
    except Exception:
        return True


@pytest.mark.deploy
def test_cant_use_list_as_BTC_USD_price():
    try:
        deploy_poor_apes_contract(["a", "b", "c"])
    except Exception:
        return True

import os
import sys
import pytest

current_wd = os.path.dirname(os.path.realpath(__file__))
scripts_path = os.path.join(current_wd, os.path.join("..", "scripts"))
sys.path.append(scripts_path)

import deploy


@pytest.fixture
def contract():
    return deploy.deploy_poor_apes_contract(19000)


@pytest.fixture
def contract_btc_above_20k():
    return deploy.deploy_poor_apes_contract(22000)


@pytest.fixture
def contract_btc_above_30k():
    return deploy.deploy_poor_apes_contract(32000)


@pytest.fixture
def contract_new_york():
    return deploy.deploy_poor_apes_contract(19000, "new_york")


@pytest.fixture
def contract_detroit():
    return deploy.deploy_poor_apes_contract(19000, "detroit")

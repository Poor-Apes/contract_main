import pytest
import deploy


@pytest.fixture
def contract():
    return deploy.deploy_poor_apes_contract(19000)


@pytest.fixture
def contract_btc_above_20k():
    return deploy.deploy_poor_apes_contract(22000)


@pytest.fixture
def contract_new_york():
    return deploy.deploy_poor_apes_contract(19000, "nyc")


@pytest.fixture
def contract_detroit():
    return deploy.deploy_poor_apes_contract(19000, "detroit")

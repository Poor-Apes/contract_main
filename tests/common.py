import pytest
import deploy


@pytest.fixture
def contract():
    return deploy.deploy_poor_apes_contract(19000)


@pytest.fixture
def contract_btc_above_20k():
    return deploy.deploy_poor_apes_contract(22000)

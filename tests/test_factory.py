import pytest
from brownie import ZERO_ADDRESS

@pytest.fixture
def implementation_address(YearnAllowlistImplementation, rando):
    return YearnAllowlistImplementation.deploy({"from": rando})

def test_clone(Allowlist, allowlist_factory, origin_name, protocol_owner_address):
    tx = allowlist_factory.cloneAllowlist(origin_name, {"from": protocol_owner_address})
    allowlist = Allowlist.at(tx.new_contracts[0])
    assert allowlist.address != ZERO_ADDRESS
    assert allowlist.name() == origin_name
    assert allowlist.ownerAddress() == protocol_owner_address

def test_clone_with_owner(Allowlist, allowlist_factory, origin_name, protocol_owner_address, rando):
    tx = allowlist_factory.cloneAllowlist(origin_name, rando, {"from": protocol_owner_address})
    allowlist = Allowlist.at(tx.new_contracts[0])
    assert allowlist.address != ZERO_ADDRESS
    assert allowlist.name() == origin_name
    assert allowlist.ownerAddress() == rando

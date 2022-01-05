import pytest
from brownie import accounts, web3

@pytest.fixture
def owner(accounts):
    yield accounts[0]

@pytest.fixture
def protocol_owner_address():
    yield web3.ens.resolve("ychad.eth")

@pytest.fixture
def rando(accounts):
    yield accounts[1]

@pytest.fixture(autouse=True)
def abiDecoder(strings, AbiDecoder, owner):
    return AbiDecoder.deploy({"from": owner})
    
@pytest.fixture(autouse=True)
def strings(Strings, owner):
    return Strings.deploy({"from": owner})
    
@pytest.fixture(autouse=True)
def introspection(Introspection, owner):
    return Introspection.deploy({"from": owner})
    
@pytest.fixture(autouse=True)
def ensHelper(EnsHelper, owner):
    return EnsHelper.deploy({"from": owner})

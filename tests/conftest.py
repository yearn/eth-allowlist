import pytest
from brownie import web3


###################
# Protocol Settings
###################

@pytest.fixture
def origin_name():
    return "yearn.finance"
    
    
###################
# Accounts
###################

@pytest.fixture
def owner(accounts):
    yield accounts[0]

@pytest.fixture
def protocol_owner_address():
    yield web3.ens.resolve("web.ychad.eth")

@pytest.fixture
def rando(accounts):
    yield accounts[1]
    
    
###################
# Libraries
###################

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

@pytest.fixture(autouse=True)
def json_writer(JsonWriter, owner):
    return JsonWriter.deploy({"from": owner})
    
    
###################
# Allowlist
###################

@pytest.fixture
def allowlist_factory(AllowlistFactory, owner, allowlist_template):
    return AllowlistFactory.deploy(allowlist_template, {"from": owner})
    
@pytest.fixture
def allowlist_registry(AllowlistRegistry, allowlist_factory, owner, rando):
    return AllowlistRegistry.deploy(allowlist_factory, {"from": owner})
    
@pytest.fixture(autouse=True)
def allowlist_validation(CalldataValidation, rando):
    return CalldataValidation.deploy({"from": rando})

@pytest.fixture
def allowlist_template(Allowlist, rando):
    return Allowlist.deploy({"from": rando})

@pytest.fixture
def allowlist(allowlist_registry, Allowlist, protocol_owner_address, origin_name, implementation_id, implementation):
    tx = allowlist_registry.registerProtocol(origin_name, {"from": protocol_owner_address})
    _allowlist = Allowlist.at(tx.new_contracts[0])
    _allowlist.setImplementation(implementation_id, implementation, {"from": protocol_owner_address})
    return _allowlist
    

###################
# Implementation
###################

@pytest.fixture
def implementation(YearnAllowlistImplementation, rando):
    return YearnAllowlistImplementation.deploy({"from": rando})
    
@pytest.fixture
def implementation_id():
    return "VAULT_VALIDATIONS"

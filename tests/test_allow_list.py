from typing import Protocol
import pytest
import brownie
from brownie import ZERO_ADDRESS, Contract

origin_name = "yearn.finance"
usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
yfi_vault_address = "0xE14d13d8B3b85aF791b2AADD661cDBd5E6097Db1"
yfi_address = "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e"
not_vault_address = "0x83d95e0D5f402511dB06817Aff3f9eA88224B030"

MAX_UINT256 = 2**256-1

@pytest.fixture
def allowlistFactory(AllowlistFactory, Allowlist, owner, rando):
    allowlist = Allowlist.deploy({"from": rando})
    return AllowlistFactory.deploy(allowlist, {"from": owner})
    
@pytest.fixture
def allowlist(allowlistFactory, Allowlist, protocol_owner_address):
    tx = allowlistFactory.startProtocolRegistration(origin_name, {"from": protocol_owner_address})
    return Allowlist.at(tx.new_contracts[0])

@pytest.fixture
def implementation_address(YearnAllowlistImplementation, rando):
    return YearnAllowlistImplementation.deploy({"from": rando})
    
def test_allowlist_factory_owner_lookup(allowlistFactory, protocol_owner_address):
    # Must be able to look up protocol owner address given an origin name
    derived_owner_address = allowlistFactory.protocolOwnerAddressByOriginName(origin_name)
    assert derived_owner_address == protocol_owner_address

def test_allowlist_factory_start_registration(allowlistFactory, Allowlist, rando, protocol_owner_address):
    # Only protocol owners can register
    with brownie.reverts():    
        allowlistFactory.startProtocolRegistration(origin_name, {"from": rando})
    tx = allowlistFactory.startProtocolRegistration(origin_name, {"from": protocol_owner_address})

    # Starting protocol registration must create a new contract
    assert len(tx.new_contracts) == 1
    allowlist_address = Allowlist.at(tx.new_contracts[0])
    assert allowlist_address != ZERO_ADDRESS
    
    # Starting protocol registration must save the protocol allowlist address
    allowlistFactory.allowlistAddressByOriginName(origin_name) == allowlist_address

def test_allowlist_factory_finish_registration(allowlistFactory, implementation_address, allowlist, protocol_owner_address):
    # Cannot finish registration without having at least one condition
    assert allowlist.conditionsLength() == 0
    with brownie.reverts():
        allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})
    
    # Owners can add valid conditions
    condition = (
        "TOKEN_APPROVE_VAULT",
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation_address
    )
    allowlist.addCondition(condition, {"from": protocol_owner_address})
    
    # Cannot finish registration if implementation is invalid
    condition_invalid = (
        "TOKEN_APPROVE_INVALID",
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "missingValidationMethod", "0"]
        ],
        implementation_address
    )
    allowlist.addConditionWithoutValidation(condition_invalid, {"from": protocol_owner_address})
    with brownie.reverts():
        allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})
    
    # Protocols with at least one valid condition must be allowed to finish registration
    allowlist.deleteCondition("TOKEN_APPROVE_INVALID", {"from": protocol_owner_address}) # Remove invalid condition
    registered_protocols = allowlistFactory.registeredProtocolsList()
    assert len(registered_protocols) == 0
    assert allowlistFactory.registeredProtocol(origin_name) == False
    allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})
    
    # Fully registered protcols must be on the registered protocols list
    registered_protocols = allowlistFactory.registeredProtocolsList()
    assert allowlistFactory.registeredProtocol(origin_name) == True
    assert len(registered_protocols) == 1
    assert registered_protocols[0] == origin_name

def test_protocol_allowlist_owner_address(allowlist, protocol_owner_address):
    # Allowlist owner address must be the address of the protocol owner
    assert allowlist.ownerAddress() == protocol_owner_address

def test_allowlist_conditions(allowlist, implementation_address, protocol_owner_address, rando):
    # Only owner can add a condition
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation_address
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT",
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ],
        implementation_address
    )
    condition_valid_2 = (
        "VAULT_DEPOSIT",
        "deposit",
        ["uint256"],
        [
            ["target", "isVaultToken"]
        ],
        implementation_address
    )
    condition_invalid_implementation = (
        "INVALID_DEPOSIT",
        "deposit",
        ["uint256"],
        [
            ["target", "invalidTest"]
        ],
        implementation_address
    )
    with brownie.reverts():
        allowlist.addCondition(condition_valid_0, {"from": rando})

    # Add a valid condition
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 1
    allowlist.addCondition(condition_valid_1, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    
    # Only owners can delete conditions
    with brownie.reverts():
        allowlist.deleteCondition("INVALID_DEPOSIT", {"from": rando})

    # Deleting conditions updates conditions list
    allowlist.deleteCondition("VAULT_DEPOSIT", {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 1

    # Adding conditions with invalid param index does not work
    condition_with_invalid_param_idx = (
        "TOKEN_APPROVE_VAULT_INVALID",
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "2"] # 0: address, 1: uint256, 2: <invalid>
        ],
        implementation_address
    )
    with brownie.reverts():
        allowlist.addCondition(condition_with_invalid_param_idx, {"from": protocol_owner_address})
        
    # Adding conditions with an invalid implementation should not work
    with brownie.reverts():
        allowlist.addCondition(condition_invalid_implementation, {"from": protocol_owner_address})
        
    # Make sure all conditions are still valid
    assert allowlist.conditionsValid() == True
    allowlist.validateConditions()

    # Only owners can add conditions without validation
    with brownie.reverts():
        allowlist.addConditionWithoutValidation(condition_invalid_implementation, {"from": rando})
    allowlist.addConditionWithoutValidation(condition_invalid_implementation, {"from": protocol_owner_address})
    
    # All conditions must now be invalid
    assert allowlist.conditionsValid() == False
    with brownie.reverts():
        allowlist.validateConditions()
    
    # Delete the invalid condition and check validity again
    allowlist.deleteCondition("INVALID_DEPOSIT", {"from": protocol_owner_address})
    assert allowlist.conditionsValid() == True
    allowlist.validateConditions()
    
    # Only owner can delete all conditions
    assert allowlist.conditionsLength() > 0
    with brownie.reverts():
        allowlist.deleteAllConditions({"from": rando})
    allowlist.deleteAllConditions({"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 0
    
    # Only owners can add multiple conditions
    with brownie.reverts():
        allowlist.addConditions([condition_valid_0, condition_valid_1], {"from": rando})
    allowlist.addConditions([condition_valid_0, condition_valid_1], {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    
    # Only owners can update conditions
    with brownie.reverts():
        allowlist.updateCondition("VAULT_DEPOSIT", condition_valid_1, {"from": rando})
    allowlist.updateCondition("VAULT_DEPOSIT", condition_valid_2, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    assert allowlist.conditionsList()[1] == condition_valid_2
    
    # Listing conditions must return data
    list = allowlist.conditionsList()
    assert len(list) == 2
    assert list[0] == condition_valid_0
    
def test_allowlist_factory_test_conditions(allowlist, implementation_address, allowlistFactory, YearnAllowlistImplementation, protocol_owner_address, rando):
    # Set up protocol allowlist
    condition = (
        "TOKEN_APPROVE_VAULT",
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation_address
    )
    allowlist.addConditionWithoutValidation(condition, {"from": protocol_owner_address})
    allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})

    # Test fetching conditions by origin name
    conditions = allowlistFactory.conditionsByOriginName(origin_name)
    assert len(conditions) > 0
    
    yfi = Contract(yfi_address)

    # Test valid calldata - token.approve(vault_address, UINT256_MAX)
    data = yfi.approve.encode_input(yfi_vault_address, MAX_UINT256)
    allowed = allowlistFactory.validateCalldata(origin_name, yfi, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_vault_address, UINT256_MAX)
    data = yfi.approve.encode_input(not_vault_address, MAX_UINT256)
    allowed = allowlistFactory.validateCalldata(origin_name, yfi, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(vault_address, UINT256_MAX)
    data = yfi.approve.encode_input(yfi_vault_address, MAX_UINT256)
    allowed = allowlistFactory.validateCalldata(origin_name, yfi_vault_address, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = yfi.decimals.encode_input()
    allowed = allowlistFactory.validateCalldata(origin_name, yfi, data)
    assert allowed == False

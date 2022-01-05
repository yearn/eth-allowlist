from typing import Protocol
import pytest
import brownie
from brownie import chain, ZERO_ADDRESS

origin_name = "yearn.finance"
usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
yfi_vault_address = "0xE14d13d8B3b85aF791b2AADD661cDBd5E6097Db1"
not_vault_address = "0x83d95e0D5f402511dB06817Aff3f9eA88224B030"

@pytest.fixture
def allowlistFactory(AllowlistFactory, owner):
    return AllowlistFactory.deploy({"from": owner})
    
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
    allowlist.deleteCondition(1, {"from": protocol_owner_address}) # Remove invalid condition
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
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ],
        implementation_address
    )
    condition_valid_1 = (
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ],
        implementation_address
    )
    condition_invalid_implementation = (
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
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    
    # Must be able to view conditions by index
    allowlist.conditions(0)
    allowlist.conditions(1)
    
    # Only owners can delete conditions
    with brownie.reverts():
        allowlist.deleteCondition(1, {"from": rando})

    # Deleting conditions updates conditions list
    allowlist.deleteCondition(1, {"from": protocol_owner_address})
    with brownie.reverts():
        allowlist.conditions(1)
    assert allowlist.conditionsLength() == 1

    # Adding conditions with invalid param index does not work
    condition_with_invalid_param_idx = (
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
        
    # Make sure implementation and conditions are still valid
    assert allowlist.implementationValid() == True
    allowlist.validateConditions()

    # Only owners can add conditions without validation
    with brownie.reverts():
        allowlist.addConditionWithoutValidation(condition_invalid_implementation, {"from": rando})
    allowlist.addConditionWithoutValidation(condition_invalid_implementation, {"from": protocol_owner_address})
    
    # Implementation must now be invalid
    assert allowlist.implementationValid() == False
    with brownie.reverts():
        allowlist.validateConditions()
    
    # Delete the invalid condition and check validity again
    allowlist.deleteCondition(1, {"from": protocol_owner_address})
    assert allowlist.implementationValid() == True
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
        allowlist.updateCondition(0, condition_valid_1, {"from": rando})
    allowlist.updateCondition(0, condition_valid_1, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    assert allowlist.conditionsList()[0] == condition_valid_1
    
    # Listing conditions must return data
    list = allowlist.conditionsList()
    assert len(list) == 2
    assert list[0] == condition_valid_1
    
def test_allowlist_factory_test_conditions(allowlist, implementation_address, allowlistFactory, YearnAllowlistImplementation, protocol_owner_address, rando):
    # Set up protocol allowlist
    condition = (
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
    
    # Test valid calldata - usdc.approve(vault_address, UINT256_MAX)
    data = "0x095ea7b3" # approve(address,uint256)
    data += "000000000000000000000000" + yfi_vault_address[2:]
    data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    allowed = allowlistFactory.validateCalldata(origin_name, usdc_address, data)
    assert allowed == True
    
    # Test invalid param - usdc.approve(not_vault_address, UINT256_MAX)
    data = "0x095ea7b3" # approve(address,uint256)
    data += "000000000000000000000000" + not_vault_address[2:]
    data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    allowed = allowlistFactory.validateCalldata(origin_name, usdc_address, data)
    assert allowed == False
    
    # Test invalid target - vault_address.approve(vault_address, UINT256_MAX)
    data = "0x095ea7b3" # approve(address,uint256)
    data += "000000000000000000000000" + yfi_vault_address[2:]
    data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    allowed = allowlistFactory.validateCalldata(origin_name, yfi_vault_address, data)
    assert allowed == False
    
    # Test invalid method - usdc.invalid(vault_address, UINT256_MAX)
    data = "0xd5bd3522" # invalid(address,uint256)
    data += "000000000000000000000000" + yfi_vault_address[2:]
    data += "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    allowed = allowlistFactory.validateCalldata(origin_name, usdc_address, data)
    assert allowed == False

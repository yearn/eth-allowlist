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

def test_allowlist_factory_finish_registration(allowlistFactory, allowlist, YearnAllowlistImplementation, rando, protocol_owner_address):
    # Cannot finish registration without
    with brownie.reverts():
        allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})

    # Cannot finish registration without having at least one condition
    implementation_address = YearnAllowlistImplementation.deploy({"from": rando})
    chain.snapshot()
    allowlist.setImplementationAddress(implementation_address, {"from": protocol_owner_address})
    with brownie.reverts():
        allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})
    chain.revert()
    
    # Adding a valid condition without validation
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addConditionWithoutValidation(condition, {"from": protocol_owner_address})
    
    # Set a valid implementation
    allowlist.setImplementationAddress(implementation_address, {"from": protocol_owner_address})
    
    # Protocols with at least one valid condition and valid implementation must be allowed to finish registration
    registered_protocols = allowlistFactory.registeredProtocolsList()
    assert len(registered_protocols) == 0
    assert allowlistFactory.registeredProtocol(origin_name) == False
    allowlistFactory.finishProtocolRegistration(origin_name, {"from": protocol_owner_address})
    assert allowlistFactory.registeredProtocol(origin_name) == True
    
    # Fully registered protcols must be on the registered protocols list
    registered_protocols = allowlistFactory.registeredProtocolsList()
    assert len(registered_protocols) == 1
    assert registered_protocols[0] == origin_name

def test_protocol_allowlist_owner_address(allowlist, protocol_owner_address):
    assert allowlist.ownerAddress() == protocol_owner_address

def test_protocol_allowlist_implementation(allowlist, YearnAllowlistImplementation, EmptyAllowlistImplementation, protocol_owner_address, rando):
    # Add a condition without validation
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addConditionWithoutValidation(condition, {"from": protocol_owner_address})

    # Only owner can set implementation
    implementation_address = YearnAllowlistImplementation.deploy({"from": rando})
    with brownie.reverts():
        allowlist.setImplementationAddress(implementation_address, {"from": rando})
    allowlist.setImplementationAddress(implementation_address, {"from": protocol_owner_address})

    # Valid implementations and conditions must pass implementation check
    assert allowlist.implementationValid() == True
    
    # Can't set an invalid implementation
    empty_implementation_address = EmptyAllowlistImplementation.deploy({"from": protocol_owner_address})
    with brownie.reverts():
        allowlist.setImplementationAddress(empty_implementation_address, {"from": protocol_owner_address})
    
    # Only owner can set an implementation without validation
    with brownie.reverts():
        allowlist.setImplementationAddressWithoutValidation(empty_implementation_address, {"from": rando})
    
    # Owner can set an invalid implementation if validation is skipped
    allowlist.setImplementationAddressWithoutValidation(empty_implementation_address, {"from": protocol_owner_address})
    
    # Invalid implementations must fail implementation validity check
    assert allowlist.implementationValid() == False
    
    # Invalid implementations must fail validation check
    with brownie.reverts():
        allowlist.validateConditions()

    # Delete all conditions
    assert allowlist.conditionsLength() > 0
    allowlist.deleteAllConditions({"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 0
    
    # Make sure implementation is valid if no conditions are present
    assert allowlist.implementationValid() == True
    allowlist.validateConditions()

def test_allowlist_conditions(allowlist, YearnAllowlistImplementation, protocol_owner_address, rando):
    # Set implementation
    implementation_address = YearnAllowlistImplementation.deploy({"from": rando})
    allowlist.setImplementationAddressWithoutValidation(implementation_address, {"from": protocol_owner_address})
    
    # Only owner can add a condition
    condition_0 = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_1 = (
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    with brownie.reverts():
        allowlist.addCondition(condition_0, {"from": rando})

    # Add a valid condition (matches implementation)
    allowlist.addCondition(condition_0, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 1
    allowlist.addCondition(condition_0, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
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
        ]
    )
    with brownie.reverts():
        allowlist.addCondition(condition_with_invalid_param_idx, {"from": protocol_owner_address})
        
    # Make sure implementation and conditions are still valid
    assert allowlist.implementationValid() == True
    allowlist.validateConditions()

    # Only owners can add conditions without validation
    with brownie.reverts():
        allowlist.addConditionWithoutValidation(condition_with_invalid_param_idx, {"from": rando})
    allowlist.addConditionWithoutValidation(condition_with_invalid_param_idx, {"from": protocol_owner_address})
    
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
        allowlist.addConditions([condition_0, condition_1], {"from": rando})
    allowlist.addConditions([condition_0, condition_1], {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    
    # Only owners can update conditions
    with brownie.reverts():
        allowlist.updateCondition(0, condition_1, {"from": rando})
    allowlist.updateCondition(0, condition_1, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    assert allowlist.conditionsList()[0] == condition_1
    
    # Listing conditions must return data
    list = allowlist.conditionsList()
    assert len(list) == 2
    assert list[0] == condition_1
    
def test_allowlist_factory_test_conditions(allowlist, allowlistFactory, YearnAllowlistImplementation, protocol_owner_address, rando):
    # Set up protocol allowlist
    condition = (
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addConditionWithoutValidation(condition, {"from": protocol_owner_address})
    implementation_address = YearnAllowlistImplementation.deploy({"from": rando})
    allowlist.setImplementationAddress(implementation_address, {"from": protocol_owner_address})
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

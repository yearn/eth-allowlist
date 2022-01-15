import brownie

def test_set_implementation(allowlist, protocol_owner_address, implementation, rando, YearnAllowlistImplementation, EmptyAllowlistImplementation, implementation_id):
    # Test initial allowlist implementation length
    assert len(allowlist.implementationsIdsList()) == 1

    # Add a condition
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_invalid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "invalid", "0"]
        ]
    )
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})

    # Updating implementation to an invalid implementation should fail
    invalid_implementation = EmptyAllowlistImplementation.deploy({"from": rando})
    with brownie.reverts():
        allowlist.setImplementation(implementation_id, invalid_implementation, {"from": protocol_owner_address})
    
    # Only allowlist owners can set implementations
    implementation_id_1 = "VAULT_VALIDATIONS_1"
    with brownie.reverts():
        allowlist.setImplementation(implementation_id_1, implementation, {"from": rando})
    allowlist.setImplementation(implementation_id_1, implementation, {"from": protocol_owner_address})
    assert allowlist.implementationsIdsList()[1] == implementation_id_1
    assert allowlist.implementationsList()[1][0] == implementation_id_1
    assert allowlist.implementationById(implementation_id_1) == implementation
    assert len(allowlist.implementationsIdsList()) == 2
    
    # Update implementation
    new_implementation = YearnAllowlistImplementation.deploy({"from": rando})
    allowlist.setImplementation(implementation_id_1, new_implementation, {"from": protocol_owner_address})
    assert len(allowlist.implementationsIdsList()) == 2
    assert allowlist.implementationById(implementation_id_1) == new_implementation

    # Add an invalid condition
    with brownie.reverts():
        allowlist.addCondition(condition_invalid_0, {"from": protocol_owner_address})

    # Create a new implementation
    implementation_id_1 = "VAULT_VALIDATIONS_2"
    allowlist.setImplementation(implementation_id_1, new_implementation, {"from": protocol_owner_address})
    ids = allowlist.implementationsIdsList()
    assert len(ids) == 3
    assert ids[2] == implementation_id_1
    

def test_add_condition(allowlist, implementation, protocol_owner_address, rando, implementation_id):
    allowlist.setImplementation(implementation_id, implementation, {"from": protocol_owner_address})

    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT_1",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    condition_with_invalid_id = (
        "TOKEN APPROVE VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_with_invalid_implementation = (
        "INVALID_DEPOSIT",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "invalidTest"]
        ]
    )
    condition_with_invalid_param_idx = (
        "TOKEN_APPROVE_VAULT_INVALID",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "2"] # 0: address, 1: uint256, 2: <invalid>
        ]
    )

    # Adding conditions with an invalid implementation should not work
    with brownie.reverts():
        allowlist.addCondition(condition_with_invalid_implementation, {"from": protocol_owner_address})    

    # Adding conditions with invalid param index does not work
    with brownie.reverts():
        allowlist.addCondition(condition_with_invalid_param_idx, {"from": protocol_owner_address})

    # Only owner can add a condition
    with brownie.reverts():
        allowlist.addCondition(condition_valid_0, {"from": rando})

    # Add a condition
    assert allowlist.conditionsLength() == 0
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})
    
    # Condition IDs cannot have spaces
    with brownie.reverts():
        allowlist.addCondition(condition_with_invalid_id, {"from": protocol_owner_address})
    
    # Make sure conditionsLength and conditionsIds are updated
    assert allowlist.conditionsLength() == 1
    assert allowlist.conditionsIds(0) == "TOKEN_APPROVE_VAULT"
    
    # Add another condition
    allowlist.addCondition(condition_valid_1, {"from": protocol_owner_address})
    
    # Make sure conditionsLength and conditionsIds are updated
    assert allowlist.conditionsIds(1) == "VAULT_DEPOSIT_1"
    
    # Conditions with duplicate IDs are not allowed
    with brownie.reverts():
        allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})

    # Only owners can add conditions without validation
    with brownie.reverts():
        allowlist.addConditionWithoutValidation(condition_with_invalid_implementation, {"from": rando})
    allowlist.addConditionWithoutValidation(condition_with_invalid_implementation, {"from": protocol_owner_address})
    
    # All conditions must now be invalid
    assert allowlist.conditionsValid() == False
    with brownie.reverts():
        allowlist.validateConditions()
        
    # Delete the invalid condition and check validity again
    allowlist.deleteCondition("INVALID_DEPOSIT", {"from": protocol_owner_address})
    assert allowlist.conditionsValid() == True
    allowlist.validateConditions()


def test_add_conditions(allowlist, implementation, protocol_owner_address, rando, implementation_id):
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT_1",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    condition_valid_2 = (
        "VAULT_DEPOSIT_2",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVaultToken"]
        ]
    )
    condition_invalid_0 = (
        "INVALID_0",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "invalid"]
        ]
    )
    condition_invalid_1 = (
        "INVALID_1",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "invalid"]
        ]
    )
    
    # Only owners can add multiple conditions
    with brownie.reverts():
        allowlist.addConditions([condition_valid_0, condition_valid_1, condition_valid_2], {"from": rando})

    # Only owners can add conditions without validation
    assert allowlist.conditionsLength() == 0
    with brownie.reverts():
        allowlist.addConditionsWithoutValidation([condition_invalid_0, condition_invalid_1], {"from": rando})
    allowlist.addConditionsWithoutValidation([condition_invalid_0, condition_invalid_1], {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    assert len(allowlist.conditionsList()) == 2
    allowlist.deleteAllConditions({"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 0

    # Add multiple conditions
    assert len(allowlist.conditionsList()) == 0
    allowlist.addConditions([condition_valid_0, condition_valid_1, condition_valid_2], {"from": protocol_owner_address})
    
    # Make sure conditionsLength, conditionsIdsList, conditionsList and conditionsIds are updated correctly
    assert allowlist.conditionsLength() == 3
    assert len(allowlist.conditionsList()) == 3
    conditionsIds = allowlist.conditionsIdsList()
    assert len(conditionsIds) == 3
    assert conditionsIds[0] == "TOKEN_APPROVE_VAULT" == allowlist.conditionsIds(0)
    assert conditionsIds[1] == "VAULT_DEPOSIT_1" == allowlist.conditionsIds(1)
    assert conditionsIds[2] == "VAULT_DEPOSIT_2" == allowlist.conditionsIds(2)
    
def test_delete_condition(allowlist, implementation_id, protocol_owner_address, rando):
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT_1",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    condition_valid_2 = (
        "VAULT_DEPOSIT_2",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVaultToken"]
        ]
    )
    
    # Add multiple conditions
    allowlist.addConditions([condition_valid_0, condition_valid_1, condition_valid_2], {"from": protocol_owner_address})
    
    # Only owners can delete conditions
    with brownie.reverts():
        allowlist.deleteCondition("VAULT_DEPOSIT_1", {"from": rando})

    # Deleting conditions updates conditions list
    assert allowlist.conditionsLength() == 3
    allowlist.deleteCondition("VAULT_DEPOSIT_1", {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 2
    
def test_delete_conditions(allowlist, implementation_id, protocol_owner_address, rando):
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT_1",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    condition_valid_2 = (
        "VAULT_DEPOSIT_2",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVaultToken"]
        ]
    )
    
    # Add multiple conditions
    allowlist.addConditions([condition_valid_0, condition_valid_1, condition_valid_2], {"from": protocol_owner_address})

    # Only owners can delete multiple conditions
    with brownie.reverts():
        allowlist.deleteConditions(["VAULT_DEPOSIT_1", "VAULT_DEPOSIT_2"], {"from": rando})
    allowlist.deleteConditions(["VAULT_DEPOSIT_1", "VAULT_DEPOSIT_2"], {"from": protocol_owner_address})
    
    # Make sure conditions list updates correctly after deleting
    assert allowlist.conditionsLength() == 1
    assert allowlist.conditionsIds(0) == "TOKEN_APPROVE_VAULT"
    assert allowlist.conditionById("TOKEN_APPROVE_VAULT")[0] == "TOKEN_APPROVE_VAULT"
    
def test_delete_all_conditions(allowlist, implementation_id, protocol_owner_address, rando):
    condition_0 = (
        "CONDITION_0",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
        ]
    )
    condition_1 = (
        "CONDITION_1",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
        ]
    )
    condition_2 = (
        "CONDITION_2",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
        ]
    )

    condition_3 = (
        "CONDITION_3",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
        ]
    )
    
    # Add conditions and check length
    allowlist.addConditions([condition_0, condition_1, condition_2, condition_3], {"from": protocol_owner_address})
    assert len(allowlist.conditionsList()) == 4
    assert allowlist.conditionsLength() == 4
    
    # Only owner can delete all conditions
    with brownie.reverts():
        allowlist.deleteAllConditions({"from": rando})
    
    # Delete all conditions and check length
    allowlist.deleteAllConditions({"from": protocol_owner_address})
    assert len(allowlist.conditionsList()) == 0
    assert allowlist.conditionsLength() == 0


def test_update_condition(allowlist, implementation_id, protocol_owner_address, rando):
    condition_valid_0 = (
        "VAULT_DEPOSIT_0",
        implementation_id,
        "deposit",
        ["uint256"],
        [
            ["target", "isVault"]
        ]
    )
    condition_valid_1 = (
        "VAULT_DEPOSIT_0",
        implementation_id,
        "deposit",
        ["uint256"],
        []
    )

    # First add a condition
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})

    # Only owners can update conditions
    assert allowlist.conditionsLength() == 1
    with brownie.reverts():
        allowlist.updateCondition(condition_valid_1, {"from": rando})
    allowlist.updateCondition(condition_valid_1, {"from": protocol_owner_address})
    assert allowlist.conditionsLength() == 1
    assert allowlist.conditionsList()[0] == condition_valid_1
    
def test_conditions_json_list(allowlist, implementation_id, protocol_owner_address):
    # Add conditions
    condition_valid_0 = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    condition_valid_1 = (
        "TOKEN_APPROVE_ZAP",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition_valid_0, {"from": protocol_owner_address})
    allowlist.addCondition(condition_valid_1, {"from": protocol_owner_address})
    assert len(allowlist.conditionsJson()) > 0
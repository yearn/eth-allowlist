from brownie import Contract

usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
yfi_vault_address = "0xE14d13d8B3b85aF791b2AADD661cDBd5E6097Db1"
yfi_address = "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e"
not_vault_address = "0x83d95e0D5f402511dB06817Aff3f9eA88224B030"

MAX_UINT256 = 2**256-1

def test_validation(allowlist, allowlist_validation, allowlist_registry, implementation_id, protocol_owner_address, origin_name):
    # Set up protocol allowlist
    condition = (
        "TOKEN_APPROVE_VAULT",
        implementation_id,
        "approve",
        ["address", "uint256"],
        [
            ["target", "isVaultToken"], 
            ["param", "isVault", "0"]
        ]
    )
    allowlist.addCondition(condition, {"from": protocol_owner_address})

    # Test valid calldata - token.approve(vault_address, UINT256_MAX)
    yfi = Contract(yfi_address)
    data = yfi.approve.encode_input(yfi_vault_address, MAX_UINT256)
    allowed = allowlist.validateCalldata(yfi, data)
    assert allowed == True
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yfi, data)
    assert allowed == True
    allowed = allowlist_validation.validateCalldataByAllowlist(allowlist, yfi, data)
    assert allowed == True
    
    # Test invalid param - token.approve(not_vault_address, UINT256_MAX)
    data = yfi.approve.encode_input(not_vault_address, MAX_UINT256)
    allowed = allowlist.validateCalldata(yfi, data)
    assert allowed == False
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yfi, data)
    assert allowed == False
    allowed = allowlist_validation.validateCalldataByAllowlist(allowlist, yfi, data)
    assert allowed == False
    
    # Test invalid target - random_contract.approve(vault_address, UINT256_MAX)
    data = yfi.approve.encode_input(yfi_vault_address, MAX_UINT256)
    allowed = allowlist.validateCalldata(yfi_vault_address, data)
    assert allowed == False
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yfi_vault_address, data)
    assert allowed == False
    allowed = allowlist_validation.validateCalldataByAllowlist(allowlist, yfi_vault_address, data)
    assert allowed == False
    
    # Test invalid method - token.decimals()
    data = yfi.decimals.encode_input()
    allowed = allowlist.validateCalldata(yfi, data)
    assert allowed == False
    allowed = allowlist_registry.validateCalldataByOrigin(origin_name, yfi, data)
    assert allowed == False
    allowed = allowlist_validation.validateCalldataByAllowlist(allowlist, yfi, data)
    assert allowed == False
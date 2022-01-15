import brownie
from brownie import ZERO_ADDRESS

def test_owner_lookup(allowlist_registry, protocol_owner_address, origin_name):
    # Must be able to look up protocol owner address given an origin name
    derived_owner_address = allowlist_registry.protocolOwnerAddressByOriginName(origin_name)
    assert derived_owner_address == protocol_owner_address
    
def test_register_protocol(allowlist_registry, Allowlist, rando, protocol_owner_address, origin_name):
    # Protocol must first not be registered
    assert len(allowlist_registry.registeredProtocolsList()) == 0
    
    # Registering a protocol only works if the origin name is valid and verified
    with brownie.reverts():
        allowlist_registry.registerProtocol("random name", {"from": protocol_owner_address})
    
    # Only protocol owners can register
    with brownie.reverts():    
        allowlist_registry.registerProtocol(origin_name, {"from": rando})
    tx = allowlist_registry.registerProtocol(origin_name, {"from": protocol_owner_address})
    
    # Registering a protocol must create a new contract
    assert len(tx.new_contracts) == 1
    allowlist = Allowlist.at(tx.new_contracts[0])
    assert allowlist.address != ZERO_ADDRESS
    
    # The new allowlist name must be equal to origin name
    assert allowlist.name() == origin_name
    
    # Registering protocols must add protocols to registeredProtocolsList
    assert len(allowlist_registry.registeredProtocolsList()) == 1
    
    # Starting protocol registration must save the protocol allowlist address
    allowlist_registry.allowlistAddressByOriginName(origin_name) == allowlist.address
    
def test_reregister_protocol(allowlist_registry, implementation_id, protocol_owner_address, origin_name, rando):
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

    # Cannot re-register and unregistered protocol
    with brownie.reverts():
        allowlist_registry.reregisterProtocol(origin_name, [condition_0, condition_1], {"from": protocol_owner_address})
        
    # Perform initial protocol registration
    allowlist_registry.registerProtocol(origin_name, {"from": protocol_owner_address})

    # Only owners can re-register protocols
    with brownie.reverts():
        allowlist_registry.reregisterProtocol(origin_name, [condition_0, condition_1], {"from": rando})
    allowlist_registry.reregisterProtocol(origin_name, [condition_0, condition_1], {"from": protocol_owner_address})

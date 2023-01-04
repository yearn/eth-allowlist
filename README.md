# Allowlist

An allowlist in this context provides the ability to store, on chain, a set of supported transactions that can be validated against, 
for example, to verify that the transaction a website is about to submit is a valid interaction with the protocol. 

Each allowlist has an array of conditions, which transactions are able to be validated against to determine their validity. If the target address and calldata satisfy at least one of the conditions
then we can confirm that the transaction is valid and can be safely executed. Data for the condition is stored in the struct below:

```
struct Condition {
  string id;
  string implementationId;
  string methodName;
  string[] paramTypes;
  string[][] requirements;
}
```

* `id` - the id of the condition, to be able to overwrite it or delete it later
* `implementationId` - the id of the implementation contract, which has validation methods to be used for validating the transaction
* `methodName` - the method name that this condition matches, e.g. `approve`
* `paramTypes` - the types of the function arguments, e.g. `[address, uint256]`
* `requirements` - the array of requirements to be met when validating the transaction and its data. The requirements are in the format `[requirement type, function name, param index]`
  * `requirement type` can be one of two values: `target` or `param`. If it's target then the proceeding function with the target address of the transaction as the argument. If it's `param` then the function is called using the on one of an argument in the calldata.
  * `function name` is the name of the function that will be called on the implementation contract to perform the validation check
  * `param index` is the index of the parameter that's being validated. If the `requirement type` is `target` then this value is not necessary to be present

Here's an example of what a condition would look like for approving a Yearn vault token:

```
{
  "id": "TOKEN_APPROVE_VAULT",
  "implementationId": "IMPLEMENTATION_YEARN_VAULTS",
  "methodName": "approve",
  "paramTypes": ["address", "uint256"],
  "requirements": [
    ["target", "isVaultUnderlyingToken"],
    ["param", "isVault", "0"]
  ]
}
```

An example of a valid transaction for approving a token with the intention of depositing it into a Yearn vault is:

target: `0x447Ddd4960d9fdBF6af9a790560d0AF76795CB08`

calldata: `0x095ea7b30000000000000000000000005c0a86a32c129538d62c106eb8115a8b02358d570000000000000000000000000000000000c097ce7bc90715b34b9f1000000000`

There are 3 steps to validate it:

1. We first check the [method selector](https://github.com/yearn/eth-allowlist/blob/03f2a9ad5716abd0dbfc6d45885f5d6a04061edc/contracts/libraries/CalldataValidation.sol#L72). From the condition we generate what we are expecting the method selector to be for an approval transaction. Since we have the function name and parameters stored in the condition we can recreate the function and take `bytes4(keccak256(bytes(reconstructedMethodSignature)))`. We can then compare this against the first 4 bytes of the calldata, to ensure that a valid function is being called by the website. The 4 byte signature of `approve(address,uint256)` is `0x095ea7b3` so we can see that the calldata is valid for this.

2. We then [validate the target](https://github.com/yearn/eth-allowlist/blob/03f2a9ad5716abd0dbfc6d45885f5d6a04061edc/contracts/libraries/CalldataValidation.sol#L50). To do this we make a call to the implementation contract of the condition, using the provided validation, in this case `isVaultUnderlyingToken`. We always know that we are validating an address so we can assume that that function has a single address parameter. It is also assumed that this function returns a `bool`. If the value returned is false then the transaction is not valid. In the implementation contract there is a function `isVaultUnderlyingToken` which then proceeds to call Yearn's vaults registry to perform the actual validation.

3. We then [validate all the parameter conditions](https://github.com/yearn/eth-allowlist/blob/03f2a9ad5716abd0dbfc6d45885f5d6a04061edc/contracts/libraries/CalldataValidation.sol#L95), of which there can be more than one, or none in the case of a function with no arguments. In this case we want to check that the parameter in position 0 satisfies the function `isVault` on the implementation contract, this way we will know that the user is depositing into a valid vault. Again, the implementation contract uses the Yearn vault registry to check whether the address decoded from the calldata is a valid vault or not.

## Who controls each website's Allowlist?
The Allowlist was designed so that each website would have an instance of its own, but we need some way on chain to link each Allowlist to each website. To do this we use ENS/DNSSEC to verify the owner of each domain - https://docs.ens.domains/dns-registrar-guide. This way we know that control of the Allowlist is linked to control of the domain, and as long as this isn't compromised the correct Allowlist for a given website can be fetched. 

The security of an Allowlist also depends on the implementation contracts. If these were easily mutable, or were implemented incorrectly, then the security of the Allowlist would be compromised. It's best to make these contracts immutable, or if they need to be updatable, then ownership by the protocol's multisig would be preferable. 

## Registering as a protocol
For protocols to create and register their own Allowlist they can do the following steps: 

* Start the registration of the Allowlist using `registerProtocol` on the [Allowlist Registry contract](https://etherscan.io/address/0xb39c4EF6c7602f1888E3f3347f63F26c158c0336). This will deploy a new Allowlist for the protocol's domain. Note: the account starting the registration will need to be registered as the owner of the domain through ENS.
* Deploy custom implementation contracts, that can be used to validate targets/parameters against
* Link these implementation contracts to the Allowlist by using the `setImplementation` function.
* Figure out all transactions that are created through the website, and create corresponding conditions. Set these conditions on the Allowlist using `addConditions`

An example deploy script can be found [here](https://github.com/yearn/yearn-allowlist/blob/main/scripts/chains/250/deploy.py)

Yearn's implementation contracts can be found in this repo here - https://github.com/yearn/yearn-allowlist

## Deployments

| Contract               | Address                                      | 
| ---------------------- | -------------------------------------------- | 
| AllowlistRegistry      | `0xb39c4EF6c7602f1888E3f3347f63F26c158c0336` |
| AllowlistFactory       | `0x383588DD317a7189522b8646b729b4B87794ccD1` |
| AllowlistTemplate      | `0x4c87E89c1215f92e9F48c1Ae2201351ce7170f01` |
| Strings                | `0xAf69afDC6b6BC0D61aBD47B3fF8999B0E0E23A27` | 
| AbiDecoder             | `0x5D7201c10AfD0Ed1a1F408E321Ef0ebc7314B086` | 
| CalldataValidation     | `0xA7e44772Ae8280698ce309F6e428De1EC3988e51` | 
| Introspection          | `0xdf3d8FF6E3F18A756e83AC23F5f8B3c8219793E8` | 
| JsonWriter             | `0x9d032763693D4eF989b630de2eCA8750BDe88219` |
| EnsHelper              | `0x93171e4237EEfAC0E29046716C65a06f44F7b809` |

// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;
import "../../interfaces/IOwnable.sol";

contract Ownable is IOwnable {
  address public ownerAddress;

  constructor() {
    ownerAddress = msg.sender;
  }

  modifier onlyOwner() {
    require(msg.sender == ownerAddress, "Ownable: caller is not the owner");
    _;
  }

  function setOwnerAddress(address _ownerAddress) public onlyOwner {
    ownerAddress = _ownerAddress;
  }
}

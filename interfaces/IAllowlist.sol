// SPDX-License-Identifier: MIT
pragma solidity 0.8.11;
import "./IOwnable.sol";

interface IAllowlist is IOwnable {
  struct Condition {
    string id;
    string implementationId;
    string methodName;
    string[] paramTypes;
    string[][] requirements;
  }

  function conditionsList() external view returns (Condition[] memory);

  function addConditions(Condition[] memory) external;

  function implementationById(string memory) external view returns (address);
}

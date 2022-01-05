// SPDX-License-Identifier: MIT

pragma solidity ^0.8.2;

library Strings {
  /**
   * @notice Search for a needle in a haystack
   * @param haystack The string to search
   * @param needle The string to search for
   */
  function stringStartsWith(string memory haystack, string memory needle)
    internal
    pure
    returns (bool)
  {
    return indexOfStringInString(needle, haystack) == 0;
  }

  /**
   * @notice Case insensitive string search
   * @param needle The string to search for
   * @param haystack The string to search
   * @return Returns -1 if no match is found, otherwise returns the index of the match
   */
  function indexOfStringInString(string memory needle, string memory haystack)
    internal
    pure
    returns (int256)
  {
    bytes memory _needle = bytes(needle);
    bytes memory _haystack = bytes(haystack);
    if (_haystack.length < _needle.length) {
      return -1;
    }
    bool _match;
    for (uint256 haystackIdx; haystackIdx < _haystack.length; haystackIdx++) {
      for (uint256 needleIdx; needleIdx < _needle.length; needleIdx++) {
        uint8 needleChar = uint8(_needle[needleIdx]);
        if (haystackIdx + needleIdx >= _haystack.length) {
          return -1;
        }
        uint8 haystackChar = uint8(_haystack[haystackIdx + needleIdx]);
        if (needleChar == haystackChar) {
          _match = true;
          if (needleIdx == _needle.length - 1) {
            return int256(haystackIdx);
          }
        } else {
          _match = false;
          break;
        }
      }
    }
    return -1;
  }

  /**
   * @notice Check to see if two strings are exactly equal
   * @dev Only valid for strings up to 32 characters
   */
  function stringsEqual(string memory input1, string memory input2)
    internal
    pure
    returns (bool)
  {
    bytes32 input1Bytes32;
    bytes32 input2Bytes32;
    assembly {
      input1Bytes32 := mload(add(input1, 32))
      input2Bytes32 := mload(add(input2, 32))
    }
    return input1Bytes32 == input2Bytes32;
  }

  function atoi(string memory a, uint8 base) public pure returns (uint256 i) {
    require(base == 2 || base == 8 || base == 10 || base == 16);
    bytes memory buf = bytes(a);
    for (uint256 p = 0; p < buf.length; p++) {
      uint8 digit = uint8(buf[p]) - 0x30;
      if (digit > 10) {
        digit -= 7;
      }
      require(digit < base);
      i *= base;
      i += digit;
    }
    return i;
  }

  function itoa(uint256 i, uint8 base) public pure returns (string memory a) {
    require(base == 2 || base == 8 || base == 10 || base == 16);
    if (i == 0) {
      return "0";
    }
    bytes memory buf = new bytes(256);
    uint256 p = 0;
    while (i > 0) {
      uint8 digit = uint8(i % base);
      uint8 ascii = digit + 0x30;
      if (digit > 9) {
        ascii += 7;
      }
      buf[p++] = bytes1(ascii);
      i /= base;
    }
    uint256 length = p;
    for (p = 0; p < length / 2; p++) {
      buf[p] ^= buf[length - 1 - p];
      buf[length - 1 - p] ^= buf[p];
      buf[p] ^= buf[length - 1 - p];
    }
    return string(buf);
  }

  function itoa16Padded(uint256 i) public pure returns (string memory) {
    string memory result = itoa(i, 16);
    if (i <= 15) {
      result = string(abi.encodePacked("0", result));
    }
    return result;
  }

  function hexStringFromBytes(bytes memory chars)
    public
    pure
    returns (string memory)
  {
    uint256 charsLength = chars.length;
    string memory result;
    for (uint256 charIdx = 0; charIdx < charsLength; charIdx++) {
      bytes1 charByte = chars[charIdx];
      string memory charStr = itoa16Padded(uint256(uint8(charByte)));
      (charByte);
      result = string(abi.encodePacked(result, charStr));
    }
    return result;
  }

  // Same as itoa16Padded.. which is more gas efficient?
  function asciiCharFromHexByte(bytes1 word)
    public
    pure
    returns (string memory)
  {
    uint8 uintWord = uint8(word);
    bytes1 msb;
    uint8 lsbUint;
    uint8 msbUint;
    assembly {
      msb := shr(4, word) // 0xAF >> 4 = 0x0A
      lsbUint := and(uintWord, 0x0F) // 0xAF & 0x0F = 0x0F
    }
    msbUint = uint8(msb);
    assembly {
      if gt(msbUint, 9) {
        msbUint := add(msbUint, 55)
      }
      if gt(lsbUint, 9) {
        lsbUint := add(lsbUint, 55)
      }
      if lt(msbUint, 10) {
        msbUint := add(msbUint, 48)
      }
      if lt(lsbUint, 10) {
        lsbUint := add(lsbUint, 48)
      }
    }
    return string(abi.encodePacked(msbUint, lsbUint));
  }
}

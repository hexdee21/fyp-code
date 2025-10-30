// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FlaggedLogStorage {
    // Struct representing a flagged transaction (stored as JSON string)
    string[] public flaggedTransactions;

    // Event for each stored transaction
    event FlaggedTransactionStored(address indexed sender, string jsonData);

    // Store a flagged transaction JSON string
    function storeFlaggedTx(string memory jsonData) public {
        flaggedTransactions.push(jsonData);
        emit FlaggedTransactionStored(msg.sender, jsonData);
    }

    // ✅ Getter function to return all stored flagged transactions
    function getAllFlaggedTxs() public view returns (string[] memory) {
        return flaggedTransactions;
    }

    // ✅ Optional helper: get total number of flagged transactions
    function getFlaggedCount() public view returns (uint256) {
        return flaggedTransactions.length;
    }
}

pragma solidity ^0.8.7;

contract groundTruth {
    uint256 public gtNum = 24;
    address public owner = msg.sender;

  event change(uint256 _before, uint256 _after);

    modifier restricted() {
    require(
      msg.sender == owner,
      "This function is restricted to the contract's owner"
    );
    _;
  }

    function changeNum()
    public restricted
    {
        gtNum = 64;
        emit change(gtNum, 64);
    }
}
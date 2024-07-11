pragma solidity >=0.8.0;

interface Test {
    function balanceOf(address user) external returns (uint256);
}

contract A {
    address[] public owners;

    constructor() {
    }

    function aaa(address a) public
    {
        Test(a).balanceOf(a);
    }

}
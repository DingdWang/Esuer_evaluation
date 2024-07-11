pragma solidity ^0.8.0;
contract test {
    function f(uint256 a, uint256 b) internal returns(uint256){
        uint256 c;
        if (a > b){
            c = a + b;
        }
        else{
            c = b + a;
        }
        return c;
    }

    function a_5(uint256 a) public returns(uint256){
        return f(a,5);
    }

    function a_b(uint256 a, uint256 b) public returns(uint256){
        return f(a,b);
    }
}
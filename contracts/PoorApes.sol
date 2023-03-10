// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

// make changes to the brownie config to import these libraries
import "@prb/contracts/PRBMathSD59x18.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract PoorApes is ERC721Enumerable, Ownable, ReentrancyGuard {
    using PRBMathSD59x18 for int256;

    using SafeMath for uint256;
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIds;
    AggregatorV3Interface public priceFeed;

    int256 public max_supply = 700;
    string public baseTokenURI;
    bool public presale = true;
    mapping(address => bool) public whitelisted;
    mapping(uint256 => uint256) private _nftType;
    uint256 public maxMintAmount = 3;
    uint256 public btc_price_in_usd = 20000 * 10 ** 8;

    /*
     * This needs to be the 46 alphanumeric string in the ipfs URL
     * to the directory containing the JSON for the NFT
     * i.e
     *    https://ipfs.io/ipfs/QmdRoeMsnbQrQXB8j4Q8iGzN14a65R1PahVPoZhJhw3KtG/2
     *                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
     *                                          ^ THIS BIT ^
     */
    constructor(
        address _priceFeed,
        string memory _IPFS_JSON_Folder
    ) ERC721("Poor Apes - Genesis", "POORG") {
        require(
            bytes(_IPFS_JSON_Folder).length == 46,
            "IPFS folder incorrect length"
        );
        priceFeed = AggregatorV3Interface(_priceFeed);
        baseTokenURI = string(
            abi.encodePacked("https://ipfs.io/ipfs/", _IPFS_JSON_Folder, "/")
        );
    }

    /**
     * Needs to be over-ridden so the resulting URI for each
     * token will be the concatenation of the 'baseURI' and the 'tokenId'
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return baseTokenURI;
    }

    // Upload the images folder
    // JSON files don't need extensions
    // The tokenURI is the location of the JSON files (without the .json extension)
    // (Example: https://ipfs.io/ipfs/QmdRoeMsnbQrQXB8j4Q8iGzN14a65R1PahVPoZhJhw3KtG/2)
    function mintNFT() public payable returns (uint256) {
        require(getBTCPrice() < btc_price_in_usd, "BTC is not under 20k usd");

        require(balanceOf(msg.sender) < maxMintAmount, "Dont be greedy!");

        if (presale) {
            require(isInWhiteList(msg.sender), "You are not in the whitelist");
        } else {
            require(
                minting_cost(-1) <= int256(msg.value),
                "More ETH required to mint NFT"
            );
        }

        require(
            _tokenIds.current() < uint256(max_supply),
            "All genesis NFTs minted"
        );

        uint256 newItemId = _tokenIds.current();
        _safeMint(msg.sender, newItemId);

        uint256 randomNumber = uint256(
            keccak256(abi.encodePacked(block.timestamp, msg.sender, newItemId))
        );

        if (randomNumber % 10 == 0) {
            _nftType[newItemId] = 1;
        } else if (randomNumber % 3 == 0) {
            _nftType[newItemId] = 2;
        } else {
            _nftType[newItemId] = 3;
        }

        _tokenIds.increment();

        return newItemId;
    }

    // Ref: https://www.desmos.com/calculator/n21xiqgmxv
    function minting_cost(int256 _nft_number) public view returns (int256) {
        int256 nft_number = _nft_number;
        if (_nft_number == -1) {
            nft_number = int256(_tokenIds.current());
        }
        if (_nft_number > max_supply) {
            nft_number = max_supply;
        }
        // in desmos z = 1.0
        int256 z = 85000000000000000; //  0.085
        int256 a = 100000000000000000; //  0.1
        int256 b = 1067000000000000000; //  1.067
        int256 c = -10000000000000000000; // -10
        //int256 d = 100000000000000000; //  0.01
        int256 cost = PRBMathSD59x18.mul(
            a,
            b.pow(PRBMathSD59x18.mul(z, (nft_number * 1000000000000000000)) + c)
        );
        return ceiling_price(cost);
    }

    function ceiling_price(int256 cost) internal pure returns (int256 result) {
        int256 scale = 1e16;
        int256 max_whole = 57896044618658097711785492504343953926634992332820282019728790000000000000000;
        require(cost <= max_whole);
        unchecked {
            int256 remainder = cost % scale;
            if (remainder == 0) {
                result = cost;
            } else {
                result = cost - remainder;
                if (cost > 0) {
                    result += scale;
                }
            }
        }
    }

    function getBTCPrice() public view returns (uint256) {
        (, int256 answer, , , ) = priceFeed.latestRoundData();
        // OLD & INCORRECT!!
        // it's already to 8 decimal places, this adds 10 more
        //return uint256(answer * 10000000000);
        // it's already to
        //return uint256(answer / (10 ** 2));
        return uint256(answer);
    }

    function withdraw() public payable onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No ether to withdraw");
        payable(owner()).transfer(balance);
    }

    function setPresale(bool _state) public onlyOwner {
        presale = _state;
    }

    function addToWhiteList(address _addr) public onlyOwner {
        require(
            _addr != owner(),
            "The owner can not be added to the whitelist"
        );
        whitelisted[_addr] = true;
    }

    function removeFromWhiteList(address _addr) public onlyOwner {
        whitelisted[_addr] = false;
    }

    function isInWhiteList(address _addr) public view returns (bool) {
        return whitelisted[_addr] || _addr == owner();
    }

    function uint2str(uint256 _i) internal pure returns (string memory str) {
        if (_i == 0) {
            return "0";
        }
        uint256 j = _i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        j = _i;
        while (j != 0) {
            bstr[--k] = bytes1(uint8(48 + (j % 10)));
            j /= 10;
        }
        str = string(bstr);
    }
}

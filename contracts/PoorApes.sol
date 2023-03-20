// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

// make changes to the brownie config to import these libraries
import "@chirulabs/contracts/ERC721A.sol";
import "@prb/contracts/PRBMathSD59x18.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract PoorApes is ERC721A, Ownable, ReentrancyGuard {
    using PRBMathSD59x18 for int256;

    using SafeMath for uint256;
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIds;
    AggregatorV3Interface public priceFeed;

    // TODO: Set ALL to start with an underscore
    int256 public max_supply = 700;
    int256 public random_number = 0;
    string public baseTokenURI;
    bool public marketing_has_withdrawn = false;
    address public _marketing_address;
    uint256 public marketing_budget_in_ETH = 10 * 10 ** 18;
    mapping(address => bool) public whitelist;
    mapping(address => bool) public whitelist_used;
    mapping(uint256 => uint256) private _nftType;
    uint256 public btc_price_in_usd = 20000 * 10 ** 8;
    // Minting curves
    uint256 public investor_minting_curve = 569900000000000000; // 0.5699
    uint256 public mover_minting_curve = 285000000000000000; //0.285

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
        address marketing_address,
        string memory _IPFS_JSON_Folder,
        int256 _random_number
    ) ERC721A("Poor Apes - Genesis", "PA-G") {
        require(
            bytes(_IPFS_JSON_Folder).length == 46,
            "IPFS folder incorrect length"
        );
        priceFeed = AggregatorV3Interface(_priceFeed);
        baseTokenURI = string(
            abi.encodePacked("https://ipfs.io/ipfs/", _IPFS_JSON_Folder, "/")
        );
        _marketing_address = marketing_address;
        random_number = random_number;
    }

    /**
     * Needs to be over-ridden so the resulting URI for each
     * token will be the concatenation of the 'baseURI' and the 'tokenId'
     */
    function _baseURI() internal view virtual override returns (string memory) {
        return baseTokenURI;
    }

    function mint() public payable returns (uint256) {
        mint(1);
    }

    // Upload the images folder
    // JSON files don't need extensions
    // The tokenURI is the location of the JSON files (without the .json extension)
    // (Example: https://ipfs.io/ipfs/QmdRoeMsnbQrQXB8j4Q8iGzN14a65R1PahVPoZhJhw3KtG/2)
    function mint(uint256 _num_nfts) public payable returns (uint256) {
        require(getBTCPrice() < btc_price_in_usd, "BTC is not under 20k usd");

        require(
            mint_cost(-1) <= int256(msg.value),
            "More ETH required to mint NFT"
        );

        uint256 newItemId = _nextTokenId();

        // 0 > 699 = 700
        require(newItemId < uint256(max_supply - 1), "All genesis NFTs minted");

        _safeMint(msg.sender, _num_nfts);

        uint256 randomNumber = uint256(
            keccak256(
                abi.encodePacked(
                    block.timestamp,
                    msg.sender,
                    newItemId,
                    random_number
                )
            )
        ) % 100;

        if (randomNumber % 10 == 0) {
            _nftType[newItemId] = 1;
        } else if (randomNumber % 3 == 0) {
            _nftType[newItemId] = 2;
        } else {
            _nftType[newItemId] = 3;
        }

        return newItemId;
    }

    function mint_cost() public view returns (int256) {
        return mint_cost(int256(_nextTokenId()));
    }

    // Ref: https://www.desmos.com/calculator/n21xiqgmxv
    function mint_cost(int256 _nft_number) public view returns (int256) {
        int256 nft_number = _nft_number;
        if (_nft_number >= max_supply - 1) {
            nft_number = max_supply - 1;
        }
        int256 z = 85000000000000000; //  0.085
        int256 a = 95000000000000000; //  0.095
        int256 b = 1068000000000000000; //  1.068
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
        return uint256(answer);
    }

    function is_mover(int256 _nft_number) public view returns (int256) {}

    function is_investor(int256 _nft_number) public view returns (int256) {}

    function is_holder(int256 _nft_number) public view returns (int256) {}

    function addToWhiteList(address _addr) public onlyOwner {
        require(
            _addr != owner(),
            "The owner can not be added to the whitelist"
        );
        whitelist[_addr] = true;
    }

    function removeFromWhiteList(address _addr) public onlyOwner {
        whitelist[_addr] = false;
    }

    function isInWhiteList(address _addr) public view returns (bool) {
        return whitelist[_addr];
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

    function withdraw_owner() public payable onlyOwner {
        uint256 balance = address(this).balance;
        require(
            _nextTokenId() == uint256(max_supply - 1),
            "Mint has not finished"
        );
        require(
            marketing_has_withdrawn == true,
            "Marketing needs to withdraw first"
        );
        require(balance > 0, "No ether to withdraw");
        payable(owner()).transfer(balance);
    }

    function withdraw_marketing() public payable {
        uint256 balance = address(this).balance;
        require(
            msg.sender == _marketing_address,
            "Only marketing can call this function"
        );
        require(
            _nextTokenId() == uint256(max_supply - 1),
            "Mint has to finish"
        );
        require(
            marketing_has_withdrawn == false,
            "Marketing has already withdrawn"
        );
        require(balance > 0, "No ether to withdraw");
        marketing_has_withdrawn = true;
        payable(owner()).transfer(marketing_budget_in_ETH);
    }
}

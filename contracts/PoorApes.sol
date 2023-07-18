// SPDX-License-Identifier: MIT

pragma solidity ^0.8.4;

// make changes to the brownie config to import these libraries
import "@chirulabs/contracts/ERC721A.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

interface FreeMintContracts {
    function balanceOf(address owner) external view returns (uint256);
}

contract PoorApes is ERC721A, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    Counters.Counter private _tokenIds;
    AggregatorV3Interface public priceFeed;

    int256 public max_supply = 0;
    int256 public max_batch = 5;
    int256 public max_batch_wl = 2;
    int256 public max_batch_free_mint_wl = 2;

    int256 public mint_price = 0;
    int256 public mint_price_whitlist = 0;
    int256 public mint_price_both_free_mints = 0;

    bool public prereveal = true;

    string private IPFS_JSON_Folder;
    string public IPFS_prereveal_JSON_Folder;

    FreeMintContracts public accessories_address;
    FreeMintContracts public accommodation_address;

    bool public marketing_has_withdrawn = false;

    address public marketing_address;
    uint256 public marketing_budget_in_ETH = 10 * 10 ** 18;

    mapping(address => bool) public whitelist;
    mapping(address => bool) public whitelist_used;

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
        string memory _name_,
        string memory _symbol_,
        address _priceFeed,
        address _marketing_address,
        address _accessories_address,
        address _accommodation_address,
        string memory _IPFS_JSON_Folder,
        string memory _IPFS_prereveal_JSON_Folder,
        int256 _max_supply,
        int256 _mint_price,
        int256 _mint_price_whitlist
    ) ERC721A(_name_, _symbol_) {
        require(
            bytes(_IPFS_JSON_Folder).length == 46,
            "IPFS folder incorrect length"
        );
        require(
            bytes(_IPFS_prereveal_JSON_Folder).length == 46,
            "IPFS pre-reveal folder incorrect length"
        );
        priceFeed = AggregatorV3Interface(_priceFeed);
        IPFS_JSON_Folder = _IPFS_JSON_Folder;
        IPFS_prereveal_JSON_Folder = _IPFS_prereveal_JSON_Folder;
        marketing_address = _marketing_address;
        accessories_address = FreeMintContracts(_accessories_address);
        accommodation_address = FreeMintContracts(_accommodation_address);
        max_supply = _max_supply;
        mint_price = _mint_price;
        mint_price_whitlist = _mint_price_whitlist;
        mint_price_both_free_mints = 0; // 50% OFF!!! Early community discount
    }

    /**
     * Needs to be over-ridden so the resulting URI for each
     * token will be the concatenation of the 'baseURI' and the 'tokenId'
     */
    function _baseURI() internal view virtual override returns (string memory) {
        string memory JSON_Folder = IPFS_prereveal_JSON_Folder;
        if (prereveal == false) {
            JSON_Folder = IPFS_JSON_Folder;
        }
        return
            string(abi.encodePacked("https://ipfs.io/ipfs/", JSON_Folder, "/"));
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
            mint_cost(int(_num_nfts)) <= int256(msg.value),
            "More ETH required to mint"
        );

        uint256 newItemId = _nextTokenId();

        // 0 > 699 = 700
        require(newItemId < uint256(max_supply - 1), "All genesis NFTs minted");

        _safeMint(msg.sender, _num_nfts);

        if (isInWhiteList(msg.sender) || ownsBothFreeMints(msg.sender)) {
            whitelist_used[msg.sender] = true;
        }

        return newItemId;
    }

    function mint_cost() public view returns (int256) {
        return mint_cost(1);
    }

    function mint_cost(int256 _num_nfts) public view returns (int256) {
        if (
            ownsBothFreeMints(msg.sender) && whitelist_used[msg.sender] == false
        ) {
            require(
                _num_nfts <= max_batch_free_mint_wl,
                "You can not mint that many NFTs (2)"
            );
            return mint_price_both_free_mints * _num_nfts;
        } else if (
            isInWhiteList(msg.sender) && whitelist_used[msg.sender] == false
        ) {
            require(
                _num_nfts <= max_batch_wl,
                "You can not mint that many NFTs (1)"
            );
            return mint_price_whitlist * _num_nfts;
        } else {
            require(
                _num_nfts <= max_batch,
                "You can not mint that many NFTs (3)"
            );
            return mint_price * _num_nfts;
        }
    }

    function getBTCPrice() public view returns (uint256) {
        (, int256 answer, , , ) = priceFeed.latestRoundData();
        return uint256(answer);
    }

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

    function disablePrereveal() public onlyOwner {
        prereveal = false;
    }

    function isInWhiteList(address _addr) public view returns (bool) {
        return whitelist[_addr];
    }

    function ownsBothFreeMints(address _addr) public view returns (bool) {
        if (
            accessories_address.balanceOf(_addr) > 0 &&
            accommodation_address.balanceOf(_addr) > 0
        ) {
            return true;
        }
        return false;
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
            msg.sender == marketing_address,
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
        uint256 dave = 10000000000000000;
        payable(marketing_address).transfer(dave);
        marketing_has_withdrawn = true;
    }
}

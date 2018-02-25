# IPFS Hash Storage in Contracts

To store an IPFS hash in a contract, you can convert the base-58 "Qm hash" that 
you're used to seeing into hex data.  Here's a couple of quick examples in 
Python and JavaScript.  I'll expand on this document later.

## Python

Basically, we're using Python's native `base58` module, and [`eth_utils` 
provided by the Etheruem Foundation](https://github.com/ethereum/eth-utils/).  
You'll need those installed.

    >>> import base58
    >>> from eth_utils.hexidecimal import decode_hex, encode_hex
    >>> # Here's our original IPFS hash
    >>> ipfs_hash = 'Qmc5gCcjYypU7y28oCALwfSvxCBskLuPKWpK4qpterKC7z'
    >>> # First, we want to decode it to Python's `bytes` type
    >>> bin_hash = base58.b58decode(ipfs_hash)
    >>> bin_hash
    b'\x12 \xcc-\x97b \x82\r\x02;qp\xf5 \xd3I\x0e\x81\x1e\xd9\x88\xae=b!GN\xe9~U\x9b\x03a'
    >>> # And we'll now use eth_utils `encode_hex` to convert form bytes to a hex 
    >>> # string we can send the contract
    >>> hex_hash = encode_hex(binHash)
    >>> hex_hash
    '0x1220cc2d976220820d023b7170f520d3490e811ed988ae3d6221474ee97e559b0361'
    >>> # Now, we have a hex string that's a bit over 32-bytes.  The good news is, 
    >>> # that there's a prefix used in this hash to tell the reader what format it
    >>> # is.  In this case, all IPFS hashes have the prefix `0x1220`, which 
    >>> # translates to the base-58 "Qm".  So we can safely ignore that since we 
    >>> # know it will always be the same.
    >>> to_contract = '0x' + hex_hash[6:]
    >>> to_contract
    '0xcc2d976220820d023b7170f520d3490e811ed988ae3d6221474ee97e559b0361'

Then you can send `to_contract` directly to a contract call.

## Javascript

The process is about the same as python, but JS has a good library for this 
called [`multihashes`](https://github.com/multiformats/js-multihash).

    > const multihashes = require('multihashes');
    undefined
    > const ipfsHash = 'Qmc5gCcjYypU7y28oCALwfSvxCBskLuPKWpK4qpterKC7z'
    undefined
    > // This is our IPFS hash
    undefined
    > // Now we convert our hash into a binary data Buffer
    undefined
    > const hashBuffer = multihashes.fromB58String('Qmc5gCcjYypU7y28oCALwfSvxCBskLuPKWpK4qpterKC7z');
    undefined
    > hashBuffer
    <Buffer 12 20 cc 2d 97 62 20 82 0d 02 3b 71 70 f5 20 d3 49 0e 81 1e d9 88 ae 3d 62 21 47 4e e9 7e 55 9b 03 61>
    > // Then we can convert it into a usable hex string
    undefined
    > const hexHash = multihashes.toHexString(hashBuffer);
    undefined
    > hexHash
    '1220cc2d976220820d023b7170f520d3490e811ed988ae3d6221474ee97e559b0361'
    > // Same as before, we don't need the prefix because it will always be
    undefined
    > // expected, so we can just chop it off.
    undefined
    > hexHash.slice(4)
    'cc2d976220820d023b7170f520d3490e811ed988ae3d6221474ee97e559b0361'
    > const toContract = '0x' + hexHash.slice(4);
    undefined

Then `toContract` can be given as input for a `bytes32` contract argument.
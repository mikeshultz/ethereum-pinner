# ethereum-pinner

**Moved to https://source.mikes.network/mikeshultz/ethereum-pinner**

Pins IPFS hashes according to events from a contract.  

Everything stored on IPFS isn't guaranteed to stay there unless a file is 
"pinned" by an IPFS node.  This pinning effectively guarantees that the file 
will always be stored on that node.  Naturally, the more distributed nodes you 
have pinning a file you need, the faster and more reliably the network can 
retrieve the file.

With a few of these pinner instances running on physically separated servers, 
you can guarantee that assets you have stored on IPFS will always be available 
in a timely manner, reducing latency and improving reliability against your file
being pruned from the network.

Using Ethereum Pinner with your dapp will allow you to "listen" for contract 
events that contain an IPFS address and they will automatically be pinned to 
the instance they're pointed at.  On startup, it will also go over all 
historical events for the contract and pin any hashes it sees, allowing you to 
add new IPFS nodes to the network as you need.

The events don't need to match any signature, but they do need to provide an 
IPFS hash as bytes32.  For example, a solidity event: 

    event FileAdded(bytes32 ipfsHash);

For details on IPFS hash conversion so it will work with storage in a contract, 
see [docs/IPFS_hash_conversion.md](docs/IPFS_hash_conversion.md).

## Install

Make sure you have an [IPFS node setup](https://ipfs.io/docs/install/) with port
`5001` open to this instance that Pinner can use to set pins.  It would probably
be best to install it to the same server instance that runs Pinner.

    python setup.py install

## Configure

Pinner needs a JSON configuration file with information on things like which 
Ethereum JSON-RPC client to use, and the contracts that should be watched.  See
the [`exampleConfig.json`](exampleConfig.json) file provided in this repository
for an example.

## Use

### Command Line

    usage: pinner-start [-h] [-d] [-p IPFS_PORT] [-t TIMEOUT] JSON IPFS_HOST

    Pin hashes for Ethereum smart contract events.

    positional arguments:
      JSON                  A JSON Configuration file
      IPFS_HOST             The root URL for an IPFS API server

    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           Show debug output
      -p IPFS_PORT, --ipfs-port IPFS_PORT
                            The IPFS API port to connect to
      -t TIMEOUT, --timeout TIMEOUT
                            The pin timeout in seconds. Default: 30

### Library

You can also use pinner as a library.

    from pinner import ContractListener
    contract = {
        "address": "0xdeadbeef...",
        "events": [{ "name": "Post", "hashParam": "contenthash"}],
        "abi": [{"anonymous":False,"inputs":[{"indexed":False,"name":"contentHash","type":"bytes32"}],"name":"Post","type":"event"}]
    }
    listener = ContractListener(contract, "http://localhost:8545/, "localhost", ipfs_port=5001)
    listener.process_events()

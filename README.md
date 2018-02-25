# ethereum-pinner

Pins IPFS hashes according to events from a contract

## Install

    python setup.py install

## Usage

### Command Line

    usage: pinner [-h] [-p IPFS_PORT] [-d] JSON IPFS_HOST

    Pin hashes for Ethereum smart contract events.

    positional arguments:
      JSON                  A JSON Configuration file
      IPFS_HOST             The root URL for an IPFS API server

    optional arguments:
      -h, --help            show this help message and exit
      -p IPFS_PORT, --ipfs-port IPFS_PORT
                            The IPFS API port to connect to
      -d, --debug           Show debug output

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
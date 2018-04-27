""" Pinner automatically pins IPFS hashes provided by Ethereum smart contract 
    events.
"""

import time
import json
import argparse
import logging
import requests
import base58
import ipfsapi
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from eth_utils.hexadecimal import decode_hex
from .decoder import EventDecoder

log = logging.getLogger('pinner')
log.setLevel(logging.DEBUG)

class Event(object):
    """ Simple event object """
    def __init__(self, name, param):
        self.name = name
        self.param = param

class ContractListener(object):
    """ ContractListener listens for events from a contract and submits pin 
        requests when needed
    """
    def __init__(self, contract, jsonrpc_server, ipfs_server, ipfs_port=5001):
        self.contract = contract
        self.server = jsonrpc_server
        self.future = Future()
        self.running = True
        self.decoder = EventDecoder(contract['abi'])
        self.ipfs = ipfsapi.connect(ipfs_server, ipfs_port)

        self.events = [x['name'] for x in self.contract['events']]
        self.event_param = {}
        for evt in self.contract['events']:
            self.events.append(evt['name'])
            self.event_param[evt['name']] = evt['hashParam']

        log.info("ContractListener initialized for %s", self.contract['address'])

        # Set the start block number if we have it
        if hasattr(self.contract, "block_number"):
            block_no = self.contract['block_number']
            if type(block_no) == int:
                block_no = hex(block_no)
            self.block_number = block_no
        else:
            self.block_number = hex(0)

    def pin(self, file_hash):
        """ Pin a file hash """
        try:
            return self.ipfs.pin_add(file_hash)
        except ipfsapi.exceptions.ErrorResponse as err:
            log.exception(str(err))

    def process_logs(self, logs):
        """ Process the logs received from JSON-RPC """
        return self.decoder.process_logs(logs)

    def process_events(self):
        """ Processes the events and pins when a new event comes in """
        
        while self.running:
            payload = {
                "method": 'eth_getLogs',
                "params": [{
                    "address": self.contract['address'],
                    "fromBlock": self.block_number,
                }],
                "id": int(time.time())
            }
            hashes = []

            log.debug(payload)

            req = requests.post(self.server, json=payload, 
                                   headers={'Content-Type': 'application/json'})

            log.debug("received logs from server")
            
            result = req.json()

            processed_events = self.process_logs(result.get('result'))

            for event in processed_events:
                if event['name'] in self.events:
                    hash_hex = event['args'][self.event_param[event['name']]]
                    ipfs_hex = '1220' + decode_hex(hash_hex).decode('utf-8')[2:]
                    b58_hash = base58.b58encode(decode_hex(ipfs_hex))
                    hashes.append(b58_hash)

            if len(hashes) > 0:
                self.block_number = hex(int(result['result'][-1]['blockNumber'], 16) + 1)
                log.debug('New start block {}'.format(self.block_number))
            log.info("Total IPFS Hashes found: %s", len(hashes))
            log.debug("Hashes found: %s", hashes)

            for h in hashes:
                log.info("Pinning %s", h)
                self.pin(h)

            time.sleep(15)

def process_contract(contract, jsonrpc_server, ipfs_server, ipfs_port=5001):
    log.debug("process_contract(%s, %s)", contract['address'], jsonrpc_server)
    listener = ContractListener(contract, jsonrpc_server, ipfs_server, ipfs_port)
    listener.process_events()
    return listener.future

def main():

    parser = argparse.ArgumentParser(description='Pin hashes for Ethereum smart contract events.')
    parser.add_argument('CONFIG', metavar='JSON', type=str, 
                        help='A JSON Configuration file')
    parser.add_argument('ipfs_host', metavar='IPFS_HOST', type=str, 
                        default='localhost',
                        help='The root URL for an IPFS API server')
    parser.add_argument('-p', '--ipfs-port', type=int, default=5001, 
                        dest="ipfs_port",
                        help="The IPFS API port to connect to")
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help="Show debug output")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    log.info("Pinner startup.")

    json_config = None
    with open(args.CONFIG) as config_file:
        json_config = json.load(config_file)

    threads = []

    log.info("Connecting to Ethereum provider {}".format(json_config['jsonrpc']))

    with ThreadPoolExecutor(max_workers=len(json_config)) as pooler:
        for contract in json_config['contracts']:
            log.debug("Starting up process for %s", contract['address'])
            threads.append(pooler.submit(process_contract, contract, json_config['jsonrpc'], args.ipfs_host, args.ipfs_port))

    for future in as_completed(threads):
        try:
            data = future.result()
        except Exception as ex:
            log.exception('Thread generated an exception: %s' % (ex))
        else:
            log.warning("Thread returned data %s", data)

if __name__ == '__main__':
    main()
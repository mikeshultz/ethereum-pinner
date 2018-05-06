""" Pinner automatically pins IPFS hashes provided by Ethereum smart contract 
    events.
"""

import time
import json
import logging
import requests
import base58
import posix_ipc
from concurrent.futures import Future
from eth_utils.hexadecimal import decode_hex
from .decoder import EventDecoder
from .pinner import QUEUE_NAME
from .utils import create_or_get_queue

log = logging.getLogger('pinner.listener')
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
    def __init__(self, contract, jsonrpc_server):
        self.contract = contract
        self.server = jsonrpc_server
        self.future = Future()
        self.running = True
        self.decoder = EventDecoder(contract['abi'])
        self.queue = None
        self.backlog = []

        try:
            self.queue = create_or_get_queue(QUEUE_NAME)
        except posix_ipc.PermissionsError as err:
            log.exception("Unable to open IPC Socket: {}".format(str(err)))
            raise err

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
        """ Add an MQ job to pin a file hash """
        log.debug("Queuing {}".format(file_hash))
        return self.queue.send(file_hash)

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
            
            try:
                result = req.json()
            except json.decoder.JSONDecodeError:
                log.error("Unexpected response from JSON-RPC server")
                result = None

            if result:

                processed_events = self.process_logs(result.get('result'))

                for event in processed_events:
                    if event['name'] in self.events:
                        hash_hex = event['args'][self.event_param[event['name']]]
                        ipfs_hex = '1220' + hash_hex[2:]
                        b58_hash = base58.b58encode(decode_hex(ipfs_hex))
                        hashes.append(b58_hash)

                if len(hashes) > 0:
                    self.block_number = hex(int(result['result'][-1]['blockNumber'], 16) + 1)
                    log.debug('New start block {}'.format(self.block_number))
                log.info("Total IPFS Hashes found: %s", len(hashes))
                log.debug("Hashes found: %s", hashes)

                for h in hashes:
                    self.pin(h)

                end = len(self.backlog)
                i = 0
                if end > 0:
                    log.debug("Trying to cleanup the backlog")
                    while h in self.backlog.pop(0):
                        i += 1
                        res = self.pin(h)
                        if res is True:
                            self.backlog.append(h)
                        # Only process the backlog once until the next iteration
                        if i >= end:
                            break

            time.sleep(15)
        self.queue.close()
        self.queue.unlink()

def process_contract(contract, jsonrpc_server):
    log.debug("process_contract(%s, %s)", contract['address'], jsonrpc_server)
    listener = ContractListener(contract, jsonrpc_server)
    listener.process_events()
    return listener.future

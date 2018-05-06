import sys
import time
import logging
import argparse
import json
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed
from .pinner import start_pinner
from .listener import process_contract

log = logging.getLogger('pinner.cli')
log.setLevel(logging.DEBUG)

def workers_alive(workers):
    for worker in workers:
        if not worker.is_alive():
            return False
    return True

def pinner(args=None):
    if not args:
        parser = argparse.ArgumentParser(description='Pin hashes for Ethereum smart contract events.')
        parser.add_argument('ipfs_host', metavar='IPFS_HOST', type=str, 
                            default='127.0.0.1',
                            help='The hostname or IP of the IPFS node. Default: 127.0.0.1')
        parser.add_argument('-p', '--ipfs-port', type=int, default=5001, 
                            dest="ipfs_port",
                            help="The IPFS API port to connect to")
        parser.add_argument('-w', '--workers', type=int, default=3, 
                            dest="workers",
                            help="Total pinner workers to start. Default: 3")
        parser.add_argument('-r', '--redis-host', type=str, default="127.0.0.1", 
                            dest="redis_host",
                            help="Redis hostname or IP address. Default: 127.0.0.1")
        parser.add_argument('-q', '--redis-port', type=int, default=6379, 
                            dest="redis_port",
                            help="Redis port. Default: 6379")
        parser.add_argument('-d', '--debug', action='store_true', default=False,
                            help="Show debug output")

        args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    log.info("Pinner startup.")

    workers = []
    for i in range(0, args.workers):
        process = mp.Process(target=start_pinner, args=(args.ipfs_host, args.ipfs_port, args.redis_host, args.redis_port))
        process.start()
        workers.append(process)

    while workers_alive(workers):
        time.sleep(1)

    log.info("Stopping pinnerworkers.")
    for worker in workers:
        if worker.is_alive():
            worker.terminate()

    log.error("Some pinner workers terminated unexpectedly!")
    sys.exit()

def listener(args=None):
    if not args:
        parser = argparse.ArgumentParser(description='Listen for IPFS hashes in Ethereum smart contract events.')
        parser.add_argument('CONFIG', metavar='JSON', type=str, 
                            help='A JSON Configuration file')
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
            threads.append(pooler.submit(process_contract, contract, json_config['jsonrpc'], args.redis_host, args.redis_port))

    for future in as_completed(threads):
        try:
            data = future.result()
        except Exception as ex:
            log.exception('Thread generated an exception: %s' % (ex))
        else:
            log.warning("Thread returned data %s", data)

    return data

def start_all():

    parser = argparse.ArgumentParser(description='Pin hashes for Ethereum smart contract events.')
    parser.add_argument('CONFIG', metavar='JSON', type=str, 
                        help='A JSON Configuration file')
    parser.add_argument('ipfs_host', metavar='IPFS_HOST', type=str, 
                        default='127.0.0.1',
                        help='The hostname or IP of the IPFS node. Default: 127.0.0.1')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help="Show debug output")
    parser.add_argument('-p', '--ipfs-port', type=int, default=5001, 
                        dest="ipfs_port",
                        help="The IPFS API port to connect to")
    parser.add_argument('-w', '--workers', type=int, default=3, 
                        dest="workers",
                        help="Total pinner workers to start. Default: 3")
    parser.add_argument('-r', '--redis-host', type=str, default="127.0.0.1", 
                        dest="redis_host",
                        help="Redis hostname or IP address. Default: 127.0.0.1")
    parser.add_argument('-q', '--redis-port', type=int, default=6379, 
                        dest="redis_port",
                        help="Redis port. Default: 6379")

    args = parser.parse_args()

    listener_instance = mp.Process(target=listener, args=(args,))
    listener_instance.start()
    pinner_instance = mp.Process(target=pinner, args=(args,))
    pinner_instance.start()

    while workers_alive([listener_instance, pinner_instance]):
        time.sleep(1)

    log.info("Stopping contract listener and pinner workers.")
    if listener_instance.is_alive():
        listener_instance.terminate()
    if pinner_instance.is_alive():
        pinner_instance.terminate()

    log.error("Execution of one of the subprocesses finished early.  Terminating...")
    sys.exit(1)

if __name__ == "__main__":
    start_all()

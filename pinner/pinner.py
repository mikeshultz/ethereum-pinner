import sys
import time
import logging
import ipfsapi
import subprocess
from .queue import RedisQueue

QUEUE_NAME = '/pinner.ipc'
TIMEOUT = 60

log = logging.getLogger('pinner.pinner')
log.setLevel(logging.DEBUG)

def quit_function(fn_name):
    log.warning('%s took too long', fn_name)
    sys.stderr.flush()
    #thread.interrupt_main()
    raise Exception("Timeout of some shit")

def pin_hash(qmHash, ipfs_server, ipfs_port=5001):
    """ Pin an ipfs hash using subprocess for timeout """
    log.debug("pin_hash")
    cmd = ['pin_one', '-p', str(ipfs_port), ipfs_server, qmHash]
    subprocess.run(cmd, timeout=TIMEOUT, check=True)
    log.debug("pin_hash+")


class Pinner(object):
    """ Listen to the message queue for IPFS files to pin """

    def __init__(self, ipfs_server, ipfs_port=5001, redis_host='localhost', redis_port=6379):
        self.ipfs = None
        self.ipfs_server = ipfs_server
        self.ipfs_port = ipfs_port
        self.queue = None
        self.backlog = []
        self.dest_pins = []

        # Connect to IPFS and be delay-tollerant for docker implementations
        ipfs_retries = 5
        ipfs_retry_count = 0
        while self.ipfs is None:
            try:
                self.ipfs = ipfsapi.connect(ipfs_server, ipfs_port)
            except ipfsapi.exceptions.ConnectionError as ex:
                if ipfs_retry_count >= ipfs_retries:
                    log.exception("Retried connection {} times.".format(ipfs_retries))
                    raise ex
                else:
                    log.debug("Error connecting to IPFS.  Retrying in 3s...")
            
            # Cool down for 3s
            time.sleep(3)

            ipfs_retry_count += 1

        self.queue = RedisQueue('hashes', host=redis_host, port=redis_port)

        # Get all of the pins on the node
        pins = self.ipfs.pin_ls(type='all').get('Keys')
        self.dest_pins = [x.encode('utf-8') for x in pins.keys()]
        log.debug("IPFS Pins on the destination node: %s", self.dest_pins)

    def process_jobs(self):
        """ Process pinner jobs from the message queue """
        while True:
            try:
                message = self.queue.pop()
                if message and message not in self.dest_pins:
                    log.debug("Starting pin thread for %s", message)
                    try:
                        pin_hash(message, self.ipfs_server, self.ipfs_port)
                        log.debug("Pinned {}".format(message))
                    except subprocess.TimeoutExpired as err:
                        log.warning("Timeout has occurred when trying to pin %s. Returning it to the queue...", message)
                        self.queue.append(message)
                    except subprocess.CalledProcessError as err:
                        log.warning("An unknown error has occurred when trying to pin %s. Returning it to the queue...", message)
                        self.queue.append(message)
                elif message in self.dest_pins:
                    log.debug("Pin exists on destination node.")
                else:
                    log.debug("No-op")
                    time.sleep(3)
            except KeyboardInterrupt:
                log.info("Shutting down at request of user...")

            log.debug("Items in backlog: %s", self.queue.qsize())

def start_pinner(ipfs_host, ipfs_port, redis_host, redis_port):
    pinner = Pinner(ipfs_host, ipfs_port, redis_host=redis_host, redis_port=redis_port)
    pinner.process_jobs()


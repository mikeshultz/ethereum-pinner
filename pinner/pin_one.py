import sys
import time
import logging
import argparse
import ipfsapi

log = logging.getLogger('pinner.pin_one')
log.setLevel(logging.DEBUG)

def main():

    ipfs_conn = None
    ipfs_retry_count = 0

    parser = argparse.ArgumentParser(description='Pin a single IPFS hash')
    parser.add_argument('ipfs_host', metavar='IPFS_HOST', type=str, 
                        default='127.0.0.1',
                        help='The hostname or IP of the IPFS node. Default: 127.0.0.1')
    parser.add_argument('ipfs_hash', type=str, metavar="HASH",
                        help="The IPFS hash to pin")
    parser.add_argument('-p', '--ipfs-port', type=int, default=5001, 
                        dest="ipfs_port",
                        help="The IPFS API port to connect to")
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help="Show debug output")
    args = parser.parse_args()

    while ipfs_conn is None:
        try:
            ipfs_conn = ipfsapi.connect(args.ipfs_host, args.ipfs_port)
        except ipfsapi.exceptions.ConnectionError as ex:
            if ipfs_retry_count >= 3:
                log.exception("Retried connection 3 times.")
                raise ex
            else:
                log.debug("Error connecting to IPFS.  Retrying in 3s...")
        
        # Cool down for 3s
        time.sleep(3)

        ipfs_retry_count += 1
    
    pinned = ipfs_conn.pin_add(args.ipfs_hash)
    if not pinned or 'Pins' not in pinned or len(pinned['Pins']) < 1:
        sys.exit(1)
    elif len(pinned['Pins']) > 0:
        print("Pinned {}".format(pinned['Pins'][0]))

if __name__ == "__main__":
    main()

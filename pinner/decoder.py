""" Event decoder utilities """
import re
import logging
import binascii
from eth_abi import decode_abi
from eth_utils import keccak, add_0x_prefix, decode_hex, encode_hex

log = logging.getLogger('pinner.decoder')

UINT_REGEX = re.compile(r'uint[0-9]{1,3}')

class EventDecoder(object):
    """ Decode events using a provided ABI and log topics """

    def __init__(self, abi, logs=None):
        self.topics = []
        self.sig_lookup = {}
        self.name_lookup = {}
        self.inputs = {}

        self.process_abi(abi)
        if logs:
            self.process_logs(logs)

    def process_abi(self, abi):
        """ Process the ABI into signatures/topics we can use """
        for part in abi:
            if part['type'] == 'event':
                indexed_list = [x['type'] for x in part['inputs'] if x.get('indexed')] 
                for i in range(0,len(indexed_list)):
                    if indexed_list[i] == 'uint':
                        indexed_list[i] = 'uint256'

                inputs_list = [x['type'] for x in part['inputs'] if not x.get('indexed')]
                for i in range(0,len(inputs_list)):
                    if inputs_list[i] == 'uint':
                        inputs_list[i] = 'uint256'

                names_list = [x['name'] for x in part['inputs']]

                inputs = ','.join([','.join(indexed_list), ','.join(inputs_list)])
                sig = "{}({})".format(part['name'], inputs)

                sig_hash = add_0x_prefix(binascii.hexlify(keccak(text=sig)).decode('utf-8'))
                self.topics.append(sig_hash)
                self.sig_lookup[sig_hash] = sig
                self.name_lookup[sig_hash] = part['name']
                self.inputs[sig_hash] = {
                    "names": names_list,
                    "indexed_types": indexed_list,
                    "data_types": inputs_list
                }

    def decode_event(self, topic, indexed, data):
        result = {}

        total_indexed = len(indexed)
        for i in range(0,total_indexed):
            this_type = self.inputs[topic]['indexed_types'][i]
            if UINT_REGEX.match(this_type):
                result[self.inputs[topic]['names'][i]] = int(indexed[i], 16)
            elif this_type in ['address', 'string', 'bytes32']:
                if this_type == 'bytes32':
                    log.debug("Decoding bytes32 value!!!!!!!!!!!!! %s", indexed[i])
                    result[self.inputs[topic]['names'][i]] = encode_hex(indexed[i])
                else:
                    result[self.inputs[topic]['names'][i]] = decode_hex(indexed[i])
            else:
                log.warn("No handler for type")


        data_vals = decode_abi(self.inputs[topic]['data_types'], data)
        for i in range(0, len(self.inputs[topic]['data_types'])):
            this_type = self.inputs[topic]['data_types'][i]
            if this_type == 'bytes32':
                result[self.inputs[topic]['names'][total_indexed+i]] = encode_hex(data_vals[i])
            else:
                result[self.inputs[topic]['names'][total_indexed+i]] = data_vals[i]

        return result

    def process_event(self, evnt): 
        """ Parse and process an event """
        topic = evnt['topics'][0]
        topic_cutoff = len(evnt['topics']) - 1
        if type(topic) != bytes:
            topic = topic.encode('utf-8')
        
        log.debug("Processing transaction %s topic %s", evnt['transactionHash'], topic)
        
        if topic in self.topics:
            decoded_event = self.decode_event(topic, evnt['topics'][1:], evnt['data'])
            event = {
                "name": self.name_lookup[topic],
                "args": decoded_event,
            }
            
            log.debug("Decoded event: %s", event)

            return event

        return None

    def process_logs(self, logs):
        """ Go through each of the provided logs and process the events """
        vals = []
        for evnt in logs:
            try:
                processed = self.process_event(evnt)
                if processed:
                    vals.append(processed)
            except Exception:
                log.exception("Unhandled error processing event")

        return vals


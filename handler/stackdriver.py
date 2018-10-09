#!/usr/bin/env python3

# Imports the Google Cloud client library
#from google.cloud import logging
import json
keys = ['sourceTransportPort', 'destinationTransportPort', 'protocolIdentifier', 'destinationMacAddress', 'postSourceMacAddress', 'sourceIPv4Address', 'destinationIPv4Address', 'ipNextHopIPv4Address', 'postNATSourceIPv4Address', 'postNATDestinationIPv4Address', 'postNAPTSourceTransportPort', 'postNAPTDestinationTransportPort', 'exporter', 'sourceTransportPortName', 'sourceTransportPortName', 'protocolIdentifierName', 'responsetime', 'flow_request', 'octetTotalCount', 'packetTotalCount', '@timestamp']
class StackDriverLogging:
    """docstring for StackDriverLogging"""
    def __init__(self, log_name):
#        print (log_name)
        from google.cloud import logging
#        import json
        # The name of the log to write to
        self.log_name = log_name

        # Instantiates a client
        logging_client = logging.Client()

        # Selects the log to write to
#        print (log_name)
        self.logger = logging_client.logger(log_name)

    def handle(self, conv):
        data = dict()
        for k in keys:
                if k in conv.keys():
                        data[k] = str(conv[k])
        # Writes the log entry
        print (json.dumps(data))
        self.logger.log_struct(data)



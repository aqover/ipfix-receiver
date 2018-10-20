#!/usr/bin/env python3

# Imports the Google Cloud client library
#from google.cloud import logging

import json
from google.cloud import logging
from influxdb import InfluxDBClient

from base.appconfig import Configuration

from datetime import datetime

class StackDriverLogging:
	"""docstring for StackDriverLogging"""
	def __init__(self, log_name):
		self.config = Configuration()

		# The name of the log to write to
		self.log_name = log_name

		# Instantiates a client
		logging_client = logging.Client()

		# Selects the log to write to
		self.logger = logging_client.logger(log_name)

		if self.config.stackdriver_logging['clear_on_start']:
			self.clear()

	def handle(self, conv):
		def getTCPFlag(flags):
			text = ''
			text += 'FIN,' if flags & 0x0001 else ''
			text += 'SYN,' if flags & 0x0002 else ''
			text += 'RST,' if flags & 0x0004 else ''
			text += 'PSH,' if flags & 0x0008 else ''
			text += 'ACK,' if flags & 0x0010 else ''
			text += 'URG,' if flags & 0x0020 else ''
			text += 'ECE,' if flags & 0x0040 else ''
			text += 'CWR,' if flags & 0x0080 else ''
			text += 'NS,' if flags & 0x0100 else ''
			return text[:-1]

		conv = self._makeStringsFromDict(conv)
		# self.logger.log_struct(conv)

		# interface, protocol, mac, ip:port , nat, len
		log = "{}, exporter: {}, in:{}, out:{}, proto:{}".format(datetime.fromtimestamp(float(conv['@timestamp'])/1000), conv['exporter'], conv['ingressInterface'], conv['egressInterface'], conv['protocolIdentifier'])

		if conv['protocolIdentifier'] == '6':
			log += '(TCP {})'.format(getTCPFlag(conv['tcpControlBits']))
		elif conv['protocolIdentifier'] == '17':
			log ++ '(UDP)'
		log += ", "

		src_mac = conv['sourceMacAddress'] if 'sourceMacAddress' in conv.keys() else conv['postSourceMacAddress']
		if src_mac != "00:00:00:00:00:00":
			log += "src-mac: {}, ".format(src_mac)

		src = "{}:{}".format(conv['sourceIPv4Address'], conv['sourceTransportPort'])
		dst = "{}:{}".format(conv['destinationIPv4Address'], conv['destinationTransportPort'])
		nat_src = "{}:{}".format(conv['postNATSourceIPv4Address'], conv['postNAPTSourceTransportPort'])
		nat_dst = "{}:{}".format(conv['postNATDestinationIPv4Address'], conv['postNAPTDestinationTransportPort'])

		log += "{}->{}, NAT {}->{}, ".format(src, dst, nat_src, nat_dst)
		log += "len: " += conv['length']

	def _makeStringsFromDict(self, dictionary):
		out = dict()
		for key in dictionary.keys():	# Native Datatypes: No Objects!
			if isinstance(dictionary[key], dict): # nested...
				out[key] = self._makeStringsFromDict(dictionary[key])
			elif not isinstance(dictionary[key], str) and not isinstance(dictionary[key], int) and not isinstance(dictionary[key], float):
				out[key] = dictionary[key].__str__()
			else:
				out[key] = dictionary[key]
		return out

	def save_many(self, datas, doctype):
		points = []
		for data in datas:
			data = self._makeStringsFromDict(data)
			if 'flow_response' in data.keys():
				flow = {
					'measurement': 'flows-{}-response'.format(doctype),
					'time': datetime.fromtimestamp(float(data['@timestamp'])/1000),
					'tags': {
						'exporter': data['exporter'],
						# 'sourceIPv6Address': data['sourceIPv6Address'],
						# 'destinationIPv6Address': data['destinationIPv6Address'],
						'sourceHostname': data['sourceHostname'],
						'destinationHostname': data['destinationHostname'],
						'destinationTransportPortName': data['destinationTransportPortName'],
						'sourceTransportPortName': data['sourceTransportPortName'],
						'protocolIdentifierName': data['protocolIdentifierName'],
						'networkLocation': data['networkLocation'],
					},
					'fields': data['flow_response'],
				}
				ponit1 = self._make_interface_stats(data['@timestamp'], data['exporter'], data['ingressInterface'], data['flow_response']['octetDeltaCount'], 0, data['flow_response']['packetDeltaCount'], 0, data['flow_response']['flowDurationMilliseconds'])
				ponit2 = self._make_interface_stats(data['@timestamp'], data['exporter'], data['egressInterface'], 0, data['flow_response']['octetDeltaCount'], 0, data['flow_response']['packetDeltaCount'], data['flow_response']['flowDurationMilliseconds'])
				
				points.append(flow)
				points.append(ponit1)
				points.append(ponit2)
				
				del data['flow_response']

			if 'flow_request' in data.keys():
				flow = {
					'measurement': 'flows-{}-request'.format(doctype),
					'time': datetime.fromtimestamp(float(data['@timestamp'])/1000),
					'tags': {
						'exporter': data['exporter'],
						# 'sourceIPv6Address': data['sourceIPv6Address'],
						# 'destinationIPv6Address': data['destinationIPv6Address'],
						'sourceHostname': data['sourceHostname'],
						'destinationHostname': data['destinationHostname'],
						'destinationTransportPortName': data['destinationTransportPortName'],
						'sourceTransportPortName': data['sourceTransportPortName'],
						'protocolIdentifierName': data['protocolIdentifierName'],
						'networkLocation': data['networkLocation'],
					},
					'fields': data['flow_request'],
				}
				ponit1 = self._make_interface_stats(data['@timestamp'], data['exporter'], data['ingressInterface'], data['flow_request']['octetDeltaCount'], 0, data['flow_request']['packetDeltaCount'], 0, data['flow_request']['flowDurationMilliseconds'])
				ponit2 = self._make_interface_stats(data['@timestamp'], data['exporter'], data['egressInterface'], 0, data['flow_request']['octetDeltaCount'], 0, data['flow_request']['packetDeltaCount'], data['flow_request']['flowDurationMilliseconds'])

				points.append(flow)
				points.append(ponit1)
				points.append(ponit2)

				del data['flow_request']

			point = {
				'measurement': 'flows-{}'.format(doctype),
				'time': datetime.fromtimestamp(float(data['@timestamp'])/1000),
				'tags': {
					'exporter': data['exporter'],
					# 'sourceIPv6Address': data['sourceIPv6Address'],
					# 'destinationIPv6Address': data['destinationIPv6Address'],
					'sourceHostname': data['sourceHostname'],
					'destinationHostname': data['destinationHostname'],
					'destinationTransportPortName': data['destinationTransportPortName'],
					'sourceTransportPortName': data['sourceTransportPortName'],
					'protocolIdentifierName': data['protocolIdentifierName'],
					'networkLocation': data['networkLocation'],
				},
				'fields': data,
			}
			points.append(point)
		influx = InfluxDBClient(self.config.influxdb['host'], self.config.influxdb['port'], self.config.influxdb['user'], self.config.influxdb['password'], self.config.influxdb['dbname'])
		influx.write_points(points)
		influx.close()

	def _make_interface_stats(self, timestamp, exporter, interface, in_byte, out_byte, in_pkt, out_pkt, duration):
		point = {
			'measurement': 'interface',
			'time': datetime.fromtimestamp(float(timestamp)/1000),
			'tags': {
				'exporter': exporter,
				'interface': interface,
			},
			'fields': {
				'in_byte': in_byte,
				'out_byte': out_byte,
				'in_packet': in_pkt,
				'out_packet': out_pkt,
				'duration': duration,
			}
		}
		return point

	def clear(self):
		self.logger.delete()



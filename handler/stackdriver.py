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

		self.influx = InfluxDBClient(self.config.influxdb['host'], self.config.influxdb['port'], self.config.influxdb['user'], self.config.influxdb['password'], self.config.influxdb['dbname'])

	def handle(self, conv):
		conv = self._makeStringsFromDict(conv)
		self.logger.log_struct(conv)

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

	def save_one(self, data, doctype):
		point = {
			'measurement': 'flows-{}'.format(doctype),
			'time': datetime.fromtimestamp(float(data['@timestamp'])/1000),
			'tags': {
				'exporter': '',
				# 'sourceIPv6Address': '',
				# 'destinationIPv6Address': '',
				'sourceHostname': '',
				'destinationHostname': '',
				'destinationTransportPortName': '',
				'sourceTransportPortName': '',
				'protocolIdentifierName': '',
				'networkLocation': '',
				'securityReason': '',
			},
			'fields': data,
		}
		for k in point['tags'].keys():
			point['tags'][k] = data[k]

		self.influx.write_points([point])

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

		self.influx.write_points(points)

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



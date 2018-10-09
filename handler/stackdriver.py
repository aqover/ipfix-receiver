#!/usr/bin/env python3

# Imports the Google Cloud client library
#from google.cloud import logging

import json
from google.cloud import logging
from influxdb import InfluxDBClient

from ipfix.information_elements import information_elements
from base.appconfig import Configuration

import ipaddress

info_keys = list(information_elements.keys())
info_values = list(information_elements.values())
influxdb_tags = ['exporter',
	"destinationIPv4Address",
	"destinationMacAddress",
	'destinationTransportPort',
	'protocolIdentifier',
	'sourceIPv4Address',
	'sourceTransportPort',
	'postNAPTDestinationTransportPort',
	'postNAPTSourceTransportPort',
	'postNATDestinationIPv4Address',
	'postNATSourceIPv4Address',
	'postSourceMacAddress']
influxdb_template = {
	"measurement": "netflow",
	"tags": dict(),
	"time": "",
	"fields": dict()
}
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
		# print (conv)
		self.save_influxdb(conv)
		# conv = self._chnageNameToIndex(conv)
		# Writes the log entry
		# print (json.dumps(data))
		self.logger.log_struct(conv)

	def _makeStringsFromDict(self, dictionary):
		out = dict()
		for key in dictionary.keys():	# Native Datatypes: No Objects!
			if isinstance(dictionary[key], dict): # nested...
				out.update((self._makeStringsFromDict(dictionary[key])))
			elif not isinstance(dictionary[key], str) and not isinstance(dictionary[key], int) and not isinstance(dictionary[key], float):
				out[key] = dictionary[key].__str__()
			else:
				out[key] = dictionary[key]
		return out

	def _chnageNameToIndex(self, dictionary):
		out = dict()
		for k in dictionary.keys():
			i = k
			if k in info_values:
				i = str(info_keys[info_values.index(k)])

			if isinstance(dictionary[k], dict): # nested...
				out[i] = self._chnageNameToIndex(dictionary[k])
			else:
				out[i] = dictionary[k]
		return out


	def save_influxdb(self, data):
		point = dict(influxdb_template)
		point['time'] = data['@timestamp']
		for k in data:
			if k in ['@timestamp']: continue
			if k in influxdb_tags:
				point['tags'][k] = data[k]
			else:
				point['fields'][k] = data[k]

		self.influx.write_points([point])

	def clear(self):
		self.logger.delete()
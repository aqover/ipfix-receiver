#!/usr/bin/env python3

# Imports the Google Cloud client library
#from google.cloud import logging

# import json
from google.cloud import logging
from influxdb import InfluxDBClient

from ipfix.information_elements import information_elements as info_ele

class StackDriverLogging:
	"""docstring for StackDriverLogging"""
	def __init__(self, log_name):
		# The name of the log to write to
		self.log_name = log_name

		# Instantiates a client
		logging_client = logging.Client()

		# Selects the log to write to
		self.logger = logging_client.logger(log_name)

	def handle(self, conv):
		data = dict()
		for k in keys:
			i = info_ele.keys()[info_ele.values().index(k)]
			if isinstance(conv[k], ipaddress):
				data[i] = str(conv[k])
			else:
				data[i] = conv[k]
		# Writes the log entry
		# print (json.dumps(data))
		self.logger.log_struct(data)

	def clear(self):
		self.logger.delete()
#!/usr/bin/env python

# Copyright 2016 Reuben Stump

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os, sys, requests, base64, json, re
from cookielib import LWPCookieJar

class NowInventory(object):
	
	def __init__(self, hostname, username, password, fields=[], groups=[]):
		self.hostname = hostname

		# requests session
		self.session = requests.Session()
		
		# request headers
		token = base64.standard_b64encode("%s:%s" % (username, password))
		self.headers = {
			"Accept": "application/json", 
			"Content-Type": "application/json", 
			"Authorization": "Basic %s" % token,
		}

		# request cookies
		self.cookies = LWPCookieJar(os.getenv("HOME") + "/.sn_api_session") 
		try:
			self.cookies.load(ignore_discard=True)
		except IOError:
			pass
		self.session.cookies = self.cookies

		# extra fields (table columns)
		self.fields = fields

		# extra groups (table columns)
		self.groups = groups

		# initialize inventory
		self.inventory = {'_meta': {'hostvars': { }}}

		return

	def __del__(self):
		self.cookies.save(ignore_discard=True)

	def _invoke(self, verb, path, data):

		# build url
		url = "https://%s/%s" % (self.hostname, path)

		# perform REST operation
		response = self.session.get(url, headers=self.headers)
		if response.status_code != 200:
			print >> sys.stderr, "http error (%s): %s" % (response.status_code, response.text)

		return response.json()

	def add_group(self, target, group):
		
		''' Transform group names:
			1. lower()
			2. non-alphanumerical characters to '_'
		'''

		group = group.lower()
		group = re.sub('\W', '_', group)

		# Ignore empty group names
		if group == '':
			return

		self.inventory.setdefault(group, {'hosts': [ ]})
		self.inventory[group]['hosts'].append(target)
		return

	def add_var(self, target, key, val):
		if not target in self.inventory['_meta']['hostvars']:
			self.inventory['_meta']['hostvars'][target] = { }
		
		
		self.inventory['_meta']['hostvars'][target]["sn_" + key] = val
		return

	def generate(self):
		table  = 'cmdb_ci_server'
		base_fields = ['name','host_name','fqdn','ip_address','sys_class_name']
		base_groups = ['sys_class_name']
		options = "?sysparm_exclude_reference_link=true&sysparm_display_value=true"
		
		columns = list(set(base_fields + base_groups + self.fields + self.groups))
		path = '/api/now/table/' + table + options + "&sysparm_fields=" + ','.join(columns)
		
		# Default, mandatory group 'sys_class_name'
		groups = list(set(base_groups + self.groups))

		content = self._invoke('GET', path, None)

		for record in content['result']:
			''' Ansible host target selection order:
				1. ip_address
				2. fqdn
				3. host_name

				TODO: environment variable configuration flags to modify selection order
			'''
			target = None
			selection = ['host_name', 'fqdn', 'ip_address']

			for k in selection:
				if record[k] != '':
					target = record[k]

			# Skip if no target available
			if target == None:
				continue

			# hostvars
			for k in record.keys():
				self.add_var(target, k, record[k])

			# groups
			for k in groups:
				self.add_group(target, record[k])

		return

	def json(self):
		return json.dumps(self.inventory)

def main(args):
	instance = os.environ['SN_INSTANCE']
	username = os.environ['SN_USERNAME']
	password = os.environ['SN_PASSWORD']

	# SN_GROUPS
	groups = os.environ.get("SN_GROUPS", [ ])
	if isinstance(groups, basestring):
		groups = groups.split(',')

	# SN_FIELDS
	fields = os.environ.get("SN_FIELDS", [ ])
	if isinstance(fields, basestring):
		fields = fields.split(',')

	inventory = NowInventory(hostname=instance, username=username, password=password, fields=fields, groups=groups)
	inventory.generate()
	print inventory.json()

if __name__ == "__main__":
	main(sys.argv)



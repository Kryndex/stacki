# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import os
import re
import subprocess
import tempfile
import time
import fcntl
import pexpect
import errno
from ipaddress import IPv4Interface, ip_network

class Switch():
	pass	


class SwitchDellX1052(Switch):
	"""Class for interfacing with a Dell x1052 switch.
	"""

	def __init__(self, switch_ip_address, username='admin', password='admin'):
		# Grab the user supplied info, in case there is a difference (PATCH)
		self.switch_ip_address = switch_ip_address
		self.username = username
		self.password = password
		self.properties_list = None
		# properties_list indices:
		self.port = 0
		self.mode = 1
		self.vlan = 2
		self.tagged = 3

		# config file dicts
		self.vlan_blocks = {}
		self.interface_blocks = {}

		self.stacki_server_ip = None
		self.netmask = None
		self.past_vlans = None
		self.new_vlans = None
		self.all_vlans = None
		self.path = '/tftpboot/pxelinux'
		self.check_filename = "%s/x1052_temp_check" % self.path
		self.download_filename = "%s/x1052_temp_download" % self.path
		self.upload_filename = "%s/x1052_temp_upload" % self.path

	def __enter__(self):
		# Entry point of the context manager
		return self

	def __exit__(self, *args):
		try:
			self.disconnect()
		except AttributeError:
			## TODO: release file lock here
			print("%s's self.child already terminated or never started." % self.switch_ip_address)

	def connect(self):
		"""Connect to the switch"""
		try:
			self.child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt ' +
									   self.switch_ip_address)
			self._expect('User Name:', 10)
			self.child.sendline(self.username)
			self._expect('Password:')
			self.child.sendline(self.password)
		except:
			print("Couldn't connect to the switch")

	def disconnect(self):
		# q will exit out of an existing scrollable more/less type of prompt
		# Probably not necessary, but a bit safer
		self.child.sendline("\nq\n")
		# exit should cleanly exit the ssh
		self.child.sendline("\nexit\n")
		# Just give it a few seconds to exit gracefully before terminate.
		time.sleep(3)
		self.child.terminate()
		

	def _expect(self, look_for, custom_timeout=15):
		try:
			self.child.expect(look_for, timeout=custom_timeout)
		except pexpect.exceptions.TIMEOUT:
			# print "Giving SSH time to close gracefully...",
			for _ in range(9, -1, -1):
				if not self.child.isalive():
					break
				time.sleep(1)
			debug_info = str(str(self.child.before) + str(self.child.buffer) + str(self.child.after))
			self.__exit__()
			raise Exception(self.switch_ip_address + " expected output '" + look_for +
							"' from SSH connection timed out after " +
							str(custom_timeout) + " seconds.\nBuffer: " + debug_info)
		except pexpect.exceptions.EOF:
			self.__exit__()
			raise Exception("SSH connection to " + self.switch_ip_address + " not available.")

	def get_mac_address_table(self):
		"""Download the file from the switch to the server"""
		print('Downloading Mac Address Table')
		start_time = int(time.time())
		time.sleep(1)
		command = 'show mac address-table'
		self.child.expect('console#', timeout=60)
		with open('/tmp/mac-address-table', 'wb') as macout:
			self.child.logfile = macout
			self.child.sendline(command)
			time.sleep(1)
			self.send_spacebar(4)
			self.child.expect('console#', timeout=60)
		self.child.logfile = None
		end_time = int(time.time())

	def send_spacebar(self, times=1):
		"""Send Spacebar; Used to read more of the output"""
		command = "\x20" * times
		self.child.send(command)

	def download(self, check=False):  # , source, destination):
		"""Download the running-config from the switch to the server"""
		time.sleep(1)
		if not check:
			_output_file = open(self.download_filename, 'w')
		else:
			_output_file = open(self.check_filename, 'w')
		os.chmod(_output_file.name, 0o777)
		_output_file.close()

		download_config = "copy running-config tftp://%s/%s" % (
			self.stacki_server_ip, 
			_output_file.name.split("/")[-1]
			)

		self.child.expect('console#', timeout=60)
		self.child.sendline(download_config)
		self._expect('The copy operation was completed successfully')

	def upload(self):
		"""Upload the file from the switch to the server"""

		upload_name = self.upload_filename.split("/")[-1]
		upload_config = "copy tftp://%s/%s temp" % (
				self.stacki_server_ip, 
				upload_name
				)
		apply_config = "copy temp running-config"
		self.child.expect('console#', timeout=60)
		self.child.sendline(upload_config)
		# Not going to look for "Overwrite file" prompt as it doesn't always show up.
		# self.child.expect('Overwrite file .temp.*\?')
		time.sleep(2)
		self.child.sendline('Y')  # A quick Y will fix the overwrite prompt if it exists.
		self._expect('The copy operation was completed successfully')
		self.child.sendline(apply_config)
		self._expect('The copy operation was completed successfully')

		self.download(True)
		# for debugging the temp files created:
		copied_file = open(self.check_filename).read()
		with open("/tftpboot/checker_file", "w") as f:
			f.write(copied_file)

		copied_file = open(self.upload_filename).read()
		with open("/tftpboot/upload_file", "w") as f:
			f.write(copied_file)


	def apply_configuration(self):
		"""Apply running-config to startup-config"""
		try:
			self.child.expect('console#')
			self.child.sendline('copy running-config startup-config')
			self.child.expect('Overwrite file .startup-config.*\?')
			self.child.sendline('Y')
			self._expect('The copy operation was completed successfully')
		except:
			raise Exception('Could not confirm configuration')
		
	def _vlan_parser(self, vlan_string):
		"""Takes input of a bunch of numbers in gives back a string containing all numbers once.
		The format for all_vlans is expected to be 3-7,9-10,44,3
		Which would be broken into a list like so: 3,4,5,6,7,9,10,44
		This if for inputing to the interface for the general port's vlan settings
		It could also be used to QA the vlans set afterwards. Which is not currently a feature."""
		clean_vlans = set()
		for each_vlan_str in vlan_string.split(","):
			if "-" in each_vlan_str:
				start, end = each_vlan_str.split("-")
				for each_number in range(int(start), int(end) + 1):
					clean_vlans.add(int(each_number))
			else:
				if each_vlan_str:
					clean_vlans.add(int(each_vlan_str))

		all_vlans = ','.join([str(vlan) for vlan in sorted(clean_vlans)])

		return all_vlans

	def write_config_block(self, config_file, port, vlans=None, frontend=False):
		""" Write Interface blocks
		interface gigabitethernet1/0/1
		 lldp optional-tlv port-desc sys-name sys-desc sys-cap 802.3-mac-phy
		!
		interface gigabitethernet1/0/19
		 switchport access vlan 2
		!
		interface gigabitethernet1/0/23
		 switchport mode general
		 switchport general allowed vlan add 2-5 tagged
		 switchport general allowed vlan add 1 untagged
		!
		"""
		config_file.write('!\n')

		if frontend:
			config_file.write('interface gigabitethernet1/0/%s\n' % port)
			config_file.write('  switchport mode general\n')
			config_file.write('  switchport general allowed vlan add %s tagged\n' % ','.join(vlans))
			config_file.write('  switchport general allowed vlan add 1 untagged\n')
		else:
			_vlan, *args = vlans
			config_file.write('interface gigabitethernet1/0/%s\n' % port)
			config_file.write('  switchport access vlan %s\n' % _vlan)


	def get_port_from_interface(self, line):
		""" Get Port from gigabitethernet interface
		interface gigabitethernet1/0/20 returns 20
		"""
		port = line.split('/')[-1]
		return port

	def update_running_config(self, hosts=None):
		"""Creates blocks to update the switch
		"""
		print("Creating the Config File")
		with open(self.upload_filename, 'w') as f:
			
			f.write('vlan 2-32\n')
			self.write_config_block(f, 19, [3])
			self.write_config_block(f, 23, [2,3,5,6,7,8], frontend=True)
			f.write('!\n')

	def parse_config(self, config_filename):
		"""Parse the given configuration file and return a list of lists describing the vlan assignments per port."""
		my_list = []
		with open(config_filename) as filename:
			lines = filename.readlines()
		for line in lines:
			if "gigabitethernet" not in line and not parse_port:
				pass
			elif "interface gigabitethernet" in line:
				parse_port = int(line.strip().split("/")[-1:][0])
			elif "interface tengigabitethernet" in line:
				parse_port = int(line.strip().split("/")[-1:][0]) + 48
			elif "!" in line:
				parse_port = None
			elif parse_port:
				parse_vlan = None
				parse_mode = None
				parse_tagged = None
				current_port_properties = [parse_port, parse_mode, parse_vlan, parse_tagged]
				if "switchport" in line:
					current_port_properties = self._parse_switchport(current_port_properties, line)
				my_list[parse_port - 1] = current_port_properties
		return my_list

	def configure(self, properties_list=None):
		"""Go through the steps to configure a switch with the config stored in the database."""
		try:
			self.update_running_config()
			self.connect()
			self.upload()
		except Exception as found_error:
			self.log.error("%s: had exception: %s" % (self.switch_ip_address, str(found_error.message)))
			self.__exit__()

	def set_tftp_ip(self, ip):
		self.stacki_server_ip = ip
# @Copyright@
# Copyright (c) 2000 - 2010 The Regents of the University of California
# All rights reserved. Rocks(r) v5.4 www.rocksclusters.org
# https://github.com/Teradata/stacki/blob/master/LICENSE-ROCKS.txt
# @Copyright@
#
# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@


import sys
import subprocess
import stack.commands
import stack.gen

class Command(stack.commands.report.command):
	"""
	Take STDIN XML input and create a shell script that can be executed
	on a host.

	<param optional='1' type='string' name='os'>
	The OS type.
	</param>

	<param optional='1' type='string' name='arch'>
	The architecture type.
	</param>

	<param optional='1' type='string' name='attrs'>
	Attributes to be used while building the output shell script.
	</param>

	<example cmd='report host interface compute-0-0 | stack report script'>
	Take the network interface XML output from 'stack report host interface'
	and create a shell script.
	</example>
	"""

	def run(self, params, args):
		osname, attrs = self.fillParams([
			('os', self.os),
			('attrs', {}) ])

		xml = ''

		if attrs:
			attrs = eval(attrs)
			xml += '<!DOCTYPE stacki-profile [\n'
			for (k, v) in attrs.items():
				xml += '\t<!ENTITY %s "%s">\n' % (k, v)
			xml += ']>\n'

		xml += '<stack:profile '
		xml += 'stack:os="%s" ' % osname
		xml += 'xmlns:stack="http://www.stacki.com" '
		xml += 'stack:attrs="%s">\n' % attrs
		xml += '<stack:post>\n'

		for line in sys.stdin.readlines():
			xml += line

		xml += '</stack:post>\n'
		xml += '</stack:profile>\n' 

		p = subprocess.Popen('/opt/stack/bin/stack list host profile profile=shell chapter=bash',
				     stdin=subprocess.PIPE,
				     stdout=subprocess.PIPE,
				     stderr=subprocess.PIPE, shell=True)
		p.stdin.write(xml.encode())
		(o, e) = p.communicate()
		if p.returncode == 0:
			sys.stdout.write(o.decode())
		else:
			sys.stderr.write(e.decode())




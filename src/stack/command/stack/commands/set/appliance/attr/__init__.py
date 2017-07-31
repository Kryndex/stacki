# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@

import stack.commands
from stack.exception import *

class Command(stack.commands.set.appliance.command):
	"""
	Sets an attribute to an appliance and sets the associated values 

	<arg type='string' name='appliance' optional='1' repeat='1'>
	Name of appliance
	</arg>
	
	<param type='string' name='attr' optional='0'>
	Name of the attribute
	</param>

	<param type='string' name='value' optional='0'>
	Value of the attribute
	</param>
	
	<param type='boolean' name='shadow'>
	If set to true, then set the 'shadow' value (only readable by root
	and apache).
	</param>

	<example cmd='set appliance attr backend attr=sge value=False'>
	Sets the sge attribution to False for backend appliances
	</example>
	"""

	def run(self, params, args):

		argv = args
		argv.append('scope=appliance')
		for p in params:
			argv.append('%s=%s' % (p, params[p]))

		self.command('set.attr', argv)


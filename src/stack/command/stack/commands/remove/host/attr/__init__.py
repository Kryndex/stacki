# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@
#
# @Copyright@
# Copyright (c) 2000 - 2010 The Regents of the University of California
# All rights reserved. Rocks(r) v5.4 www.rocksclusters.org
# https://github.com/Teradata/stacki/blob/master/LICENSE-ROCKS.txt
# @Copyright@

import stack.commands

class Command(stack.commands.remove.host.command):
	"""
	Remove an attribute for a host.

	<arg type='string' name='host' optional='1' repeat='1'>
	One or more hosts
	</arg>
	
	<param type='string' name='attr' optional='0'>
	The attribute name that should be removed.
	</param>
	
	<example cmd='remove host attr backend-0-0 attr=cpus'>
	Removes the attribute cpus for host backend-0-0.
	</example>
	"""

	def run(self, params, args):
		self.command('set.attr', self._argv + [ 'scope=host', 'value=' ])
		return self.rc

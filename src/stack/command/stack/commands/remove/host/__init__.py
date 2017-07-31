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
from stack.exception import *

class command(stack.commands.HostArgumentProcessor,
		stack.commands.remove.command):
	pass

class Command(command):
	"""
	Remove a host from the database. This command will remove all
	related database rows for each specified host.

	<arg type='string' name='host' repeat='1'>
	List of hosts to remove from the database.
	</arg>

	<example cmd='remove host backend-0-0'>
	Remove the backend-0-0 from the database.
	</example>
	"""

	def run(self, params, args):
		if len(args) < 1:
			raise ArgRequired(self, 'host')

		me    = self.db.getHostname()
		hosts = self.getHostnames(args)

		# Don't allow the user to remove the host the command
		# is running on.  Right now that means cannot remove
		# the Frontend, but checked this way will allow for
		# future multiple Frontend's where you may still want 
		# to remove some but not all of them.

		if me in hosts:
			raise CommandError(self, 'cannot remove "%s"' % me)

		self.runPlugins(hosts)

		#	
		# sync the config when done
		#	
		self.command('sync.config')


# @SI_Copyright@
# Copyright (c) 2006 - 2017 StackIQ Inc.
# All rights reserved. stacki(r) v4.0 stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @SI_Copyright@
#
#

import os
import sys
import stack.commands

class Plugin(stack.commands.Plugin):
	"Writes DNS configuration"

	def provides(self):
		return 'dns'

	def run(self, args):
		self.owner.command('sync.dns',[])


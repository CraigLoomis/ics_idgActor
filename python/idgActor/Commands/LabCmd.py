#!/usr/bin/env python

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

class LabCmd(object):

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('lab', '@raw', self.raw),
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("labpc.labpc", (1, 1),
                                        )


    def raw(self, cmd):
        """Report camera status and actor version. """

        try:
            dev = self.actor.labpc
        except Exception, e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        ret = dev.sendOneCommand(cmd.cmd.keywords['raw'].values[0],
                                 cmd=cmd)
        
        cmd.inform('text="returned %s"' % (ret))
        cmd.finish()


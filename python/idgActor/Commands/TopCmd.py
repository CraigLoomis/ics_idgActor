#!/usr/bin/env python

from builtins import object
import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

class TopCmd(object):

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('connect', '', self.connect),
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("mcs_mcs", (1, 1),
                                        )
    def controllerKey(self):
        controllerNames = list(self.actor.controllers.keys())
        key = 'controllers=%s' % (','.join([c for c in controllerNames]))

        return key
    
    def connect(self, cmd, doFinish=True):
        """ Reload all controller objects. """

        controller = 'labpc'
        instanceName = None
        try:
            self.actor.attachController(controller,
                                        instanceName=instanceName)
        except Exception as e:
                cmd.fail('text="failed to connect controller %s: %s"' % (instanceName,
                                                                         e))
                return

        cmd.finish(self.controllerKey())
        

    def ping(self, cmd):
        """Query the actor for liveness/happiness."""

        cmd.warn("text='I am an empty and fake actor'")
        cmd.finish("text='Present and (probably) well'")

    def status(self, cmd):
        """Report camera status and actor version. """

        self.actor.sendVersionKey(cmd)
        
        cmd.inform('text="Present!"')
        cmd.finish()


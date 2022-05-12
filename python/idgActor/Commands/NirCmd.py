#!/usr/bin/env python

import opscore.protocols.keys as keys
import opscore.protocols.types as types

class NirCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('nirstatus', '', self.status),
            #('nirled', 'off', self.ledOff),
            #('nirled', '<wave> <cycle>', self.ledOn),
            #('nirmove', '<pix>', self.moveToPix),
            #('nirmove', '<steps>', self.moveToSteps),
            ('temps', 'status', self.tempsStatus),
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("idg_nir", (1, 1),
                                        keys.Key("wave", types.Enum(930,970,1030,1085,1200,1300),
                                                 help='select LED by wavelength'),
                                        keys.Key("cycle", types.Int(),
                                                 help='duty cycle for LED'),
                                        keys.Key("pix", types.Float()*2,
                                                 help='pixel to move to'),
                                        keys.Key("steps", types.Int()*2,
                                                 help='motor steps to move to'),
                                        )

    @property
    def controller(self):
        return self.actor.controllers.get('nir', None)
    
    def status(self, cmd):
        """Report camera status and actor version. """

        nir = self.controller
        if nir is None:
            cmd.fail('text="NIR cleanroom controller is not connected. Try `connect controller=nir`"')
            return

        
        self.actor.sendVersionKey(cmd)
        
        cmd.inform('text="Present!"')
        cmd.finish()

    def tempsStatus(self, cmd):
        """Command the second SMB for the NIR cleanroom thermal plate tests."""        
        cmdStr = "?t"
        ret = self.actor.controllers['temps'].tempsCmd(cmdStr, cmd=cmd) 

        temps = ret.split(',')
        cmd.finish('thermalTemps=%s' % ', '.join(['%0.4f' % (float(t)) for t in temps[:6]]))

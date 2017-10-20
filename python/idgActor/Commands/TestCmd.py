#!/usr/bin/env python

import time

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

class TestCmd(object):

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('motors', 'checkRepeats <cam> [<reps>] [<axis>] [<distance>] [<delay>]', self.checkRepeats),
            ('motors', 'findRange <cam> [<current>] [<axis>]', self.findRange),
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("test.test", (1, 1),
                                        keys.Key("cam", types.String(),
                                                 help='camera name, e.g. b2'),
                                        keys.Key("axis", types.Enum('a','b','c'), default=None,
                                                 help='axis name'),
                                        keys.Key("reps", types.Int(), default=1,
                                                 help='number of repetitions'),
                                        keys.Key("delay", types.Float(), default=60,
                                                 help='delay between repetitions'),
                                        keys.Key("distance", types.Int(), default=300,
                                                 help='how far to move'),
                                        keys.Key("current", types.Int(),
                                                 help='motor current override'),
                                        
                                        )

    def safeCmd(self, cmd, actor, cmdString, timeLim=None):
        cmdVar = self.actor.cmdr.call(actor=actor, cmdStr=cmdString,
                                      forUserCmd=cmd, timeLim=timeLim)
        if cmdVar.didFail:
            raise RuntimeError('command %s %r failed' % (actor, cmdString))
            # cmd.fail('text=%s' % (qstr('Failed to expose with %s' % (cmdString))))
            # return None

        return cmdVar

    def grabPositions(self, cmd, actor, legend):
        model = self.actor.models[actor]
        ret = self.safeCmd(cmd, actor, "motors status", timeLim=5)
        positions = []
        homeSwitches = []
        farSwitches = []
        for i in range(3):
            keyName = 'ccdMotor%d' % (i+1)
            posKey = getattr(model, keyName)
            homeSwitch = posKey[1]
            farSwitch = posKey[2]
            posVal = posKey[3]

            positions.append(posVal)
            homeSwitches.append(homeSwitch)
            farSwitches.append(farSwitch)
            cmd.inform('text="test %s %d %s %s %d"' % (legend, i+1,
                                                       homeSwitch, farSwitch, posVal))

        return positions, homeSwitches, farSwitches
        
    def motorHome(self, cmd, cam, motor, doFinish=True):
        pass
    
    def checkRepeats(self, cmd):
        """ check how repeatable motion is. 

        1. home axes
        2. slew out the given distance
        3. slew back to near the home switch.
        4. inch onto the home switch. Report distance from home.
        5. cool off
        6. optionally repeat
        """

        keys = cmd.cmd.keywords
        cam = keys['cam'].values[0]
        axis = keys['axis'].values[0] if 'axis' in keys else None
        reps = keys['reps'].values[0] if 'reps' in keys else 1
        delay = keys['delay'].values[0] if 'delay' in keys else 60
        farDist = keys['distance'].values[0] if 'distance' in keys else 3000

        nearDist = 30
        actor = 'xcu_%s' % (cam)

        if axis is None:
            allAxes = 'a', 'b', 'c'
            moveAxis = 'piston'
        else:
            allAxes = axis,
            moveAxis = axis

        cmd.inform('text="starting %d-cycle loop on %s:%s...."' % (reps, cam, str(allAxes)))
            
        self.safeCmd(cmd, actor, "motors init", timeLim=5)
        self.safeCmd(cmd, actor, "motors home", timeLim=60)
        self.grabPositions(cmd, actor, 'initial home')

        for i in range(reps):
            if axis is None:
                self.safeCmd(cmd, actor, "motors home", timeLim=60)
            else:
                self.safeCmd(cmd, actor, "motors home axes=%s" % (axis), timeLim=60)
            self.grabPositions(cmd, actor, '%d home' % (i))
            time.sleep(1)
            self.safeCmd(cmd, actor, "motors move %s=%d" % (moveAxis, farDist), timeLim=30)
            time.sleep(1)
            self.safeCmd(cmd, actor, "motors move %s=%d abs" % (moveAxis, nearDist), timeLim=30)
            self.grabPositions(cmd, actor, '%d near' % (i))

            for ax in allAxes:
                self.safeCmd(cmd, actor, "motors toSwitch %s home set" % (ax), timeLim=15)
            self.grabPositions(cmd, actor, '%d onSwitch' % (i))
            
            for ax in allAxes:
                self.safeCmd(cmd, actor, "motors toSwitch %s home clear" % (ax), timeLim=15)
            final = self.grabPositions(cmd, actor, '%d offSwitch' % (i))
            offsets = [final[0][a_i] - 100 for a_i in range(3)]
            cmd.inform('testOffsets=%s,%d,%d,%d,%d' % (cam, i,
                                                       offsets[0], offsets[1], offsets[2]))
            if i < reps-1:
                cmd.inform('text="cooling down for %s seconds...."' % (delay))
                time.sleep(delay)
                
        self.safeCmd(cmd, actor, "motors home", timeLim=60)
        cmd.finish('text="done and homed"')

    def findRange(self, cmd):
        """ Measure full range of motor motion. 

        1. home axes
        2. slam into far limit
        3. inch off the far limit
        4. note position
        5. slew back near the home switch
        6. inch onto home switch.
        7. note position
        8. home

        """

        keys = cmd.cmd.keywords
        cam = keys['cam'].values[0]
        current = keys['current'].values[0] if 'current' in keys else None
        actor = 'xcu_%s' % (cam)
        axes = 'a','b','c'
        
        farDist = 5000          # Onto far switch
        nearDist = 25
        
        self.safeCmd(cmd, actor, "motors init", timeLim=5)

        if current is not None:
            cmd.warn('test="overriding current to %d percent."' % (current))
            for ax_i, ax in enumerate(axes):
                self.safeCmd(cmd, actor, 'motors raw=aM%dm%dR' % (ax_i+1, current))
                
        self.safeCmd(cmd, actor, "motors move piston=%d" % (farDist), timeLim=30)
        ret = self.grabPositions(cmd, actor, 'tooFar')
        if not all(ret[-1]):
            cmd.warn('text="some axes are not on far limit: %s' % (ret[-1]))
        time.sleep(1)
        for ax in axes:
            ret = self.safeCmd(cmd, actor, "motors toSwitch %s far clear" % (ax), timeLim=60)
        offFar = self.grabPositions(cmd, actor, 'offFar')
        if any(offFar[-1]):
            cmd.warn('text="some axes are not off far limit: %s' % (offFar[-1]))


        ret = self.safeCmd(cmd, actor, "motors move piston=%d abs force" % (nearDist), timeLim=30)
        self.grabPositions(cmd, actor, 'nearHome')

        for ax in axes:
            ret = self.safeCmd(cmd, actor, "motors toSwitch %s home set" % (ax), timeLim=15)
        onHome = self.grabPositions(cmd, actor, 'onSwitch')
        if not all(onHome[1]):
            cmd.warn('text="some axes are not on home limit: %s' % (onHome[1]))

        ranges = [offFar[0][i] - onHome[0][i] - 1 for i in range(3)]
        
        ret = self.safeCmd(cmd, actor, "motors home", timeLim=60)
        cmd.finish('testRange=%s,%d,%d,%d' % (cam, ranges[0], ranges[1], ranges[2]))

#!/usr/bin/env python

import time

import opscore.protocols.keys as keys
import opscore.protocols.types as types
from opscore.utility.qstr import qstr

import numpy as np
import pandas as pd

class KeithleyCmd(object):

    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('current', '@raw', self.raw),
            ('current', 'read [<chan>] [<nread>]', self.read),
            ('current', 'init', self.init),
            ('n8pds', 'meas <name> [<wave>] [<power>] [<nread>] [<note>]', self.n8pds)
        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("keithley.keithley", (1, 1),
                                        keys.Key("chan", types.Int(),
                                                 help='channel number'),
                                        keys.Key("wave", types.Float(),
                                                 help='LED wavelength'),
                                        keys.Key("power", types.Float(),
                                                 help='LED power'),
                                        keys.Key("nread", types.Int(),
                                                 help='number of readings'),
                                        keys.Key("name", types.String(),
                                                 help='experiment name '),
                                        keys.Key("note", types.String(),
                                                 help='channel number, '),

                                        )

    @property
    def keithley(self):
        return self.actor.controllers['keithley']

    def raw(self, cmd):
        """Report camera status and actor version. """

        try:
            dev = self.keithley
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        ret = dev.sendOneCommand(cmd.cmd.keywords['raw'].values[0],
                                 cmd=cmd)

        cmd.inform('text="returned %s"' % (ret))
        cmd.finish()

    def init(self, cmd):
        try:
            dev = self.keithley
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        cmdList = ['SENS1:CURR:NPLC 1',
                   'SYST:AZER ON',
                   'SOUR1:GCON OFF',
                   'SOUR2:GCON OFF',
                   'SOUR1:VOLT:MODE FIX',
                   'SOUR2:VOLT:MODE FIX',
                   'SOUR1:VOLT:RANG 10',
                   'SOUR2:VOLT:RANG 10',
                   'SOUR1:VOLT 0',
                   'SOUR2:VOLT 0',
                   'OUTP1 OFF',
                   'OUTP2 OFF',
                   'SENS1:CURR:RANG:AUTO ON',
                   'SENS2:CURR:RANG:AUTO ON',
                   'CALC5:FORM C4C3']

        for c in cmdList:
            dev.sendOneCommand(c, cmd=cmd, noResponse=True)
        cmd.finish()

    def read(self, cmd):
        cmdKeys = cmd.cmd.keywords
        if 'chan' in cmdKeys:
            chan = int(cmdKeys['chan'].values[0])
            if chan not in {1,2}:
                cmd.fail('text="chan must be 1 or 2')
                return
            chans = [chan]
        else:
            chans = [1,2]

        for c in chans:
            meas = self.current(c, cmd=cmd)
            cmd.inform(f'text="chan {c}: {meas}"')
        cmd.finish()

    def n8pds(self, cmd):
        cmdKeys = cmd.cmd.keywords
        wave = cmdKeys['wave'].values[0] if 'wave' in cmdKeys else -9999
        power = cmdKeys['power'].values[0] if 'power' in cmdKeys else -9999
        nread = cmdKeys['nread'].values[0]  if 'nread' in cmdKeys else 7
        name = cmdKeys['name'].values[0]
        note = cmdKeys['note'].values[0] if 'note' in cmdKeys else ''
        note = note.replace(' ', '_')

        ledmap = {}
        dfRows = []
        chans = [1,2]
        for c in chans:
            meas = self.current(c, cmd=cmd, number_keithley_reads=nread)
            ts = time.strftime("%Y-%m-%dT%H:%M:%S")
            cmd.inform(f'text="chan {c}: {np.median(np.array(meas))} {meas}"')
            for m_i, m in enumerate(meas):
                dfRows.append(dict(ts=ts, name=name, chan=c, wavelength=wave, power=power,
                                   reading=m_i, value=m,
                                   note=note))
        df = pd.DataFrame(dfRows)
        fname = f'/data/pfseng/n8_photodiode/pdmeas_{name}_{ts}.txt'
        with open(fname, 'at') as f:
            f.write(df.to_string() + '\n')
        cmd.finish(f'text="wrote {fname}"')

    def current(self, current_number=1, number_keithley_reads=7, cmd=None):
        try:
            dev = self.keithley
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        cmds = ('TRAC:POIN %2i' % number_keithley_reads,
                'TRAC:FEED:CONT NEXT',
                'TRIG:COUN %2i' % number_keithley_reads,
                'FORM:ELEM:TRAC CURR%s' % str(current_number),
                'INIT')
        for c in cmds:
            ret = dev.sendOneCommand(c, cmd=cmd, noResponse=True)

        readCmd = 'TRACE:DATA?'
        ret = dev.sendOneCommand(readCmd, cmd=cmd)
        data_current_split = tuple(map(float, ret.split(',')))

        return data_current_split



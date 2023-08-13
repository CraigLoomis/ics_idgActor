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
            ('current2', '@raw', self.raw2),
            ('current2', 'init', self.init2),
            # ('current', '@(one|two)'), self.defKeithleys),
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
                                                 help='number of internal readings'),
                                        keys.Key("name", types.String(),
                                                 help='experiment name '),
                                        keys.Key("note", types.String(),
                                                 help='channel number, '),

                                        )

        self.ledIds = {940:1, 1050:2, 1200:3, 1300:4}

    @property
    def keithley(self):
        return self.actor.controllers['keithley']
    @property
    def keithley2(self):
        return self.actor.controllers['keithley2']

    def device(self, channel):
        if channel == 1:
            return self.keithley
        elif channel == 2:
            return self.keithley2
        else:
            raise ValueError(f"invalid channel: {channel}")

    def _raw(self, cmd, channel):
        """Report camera status and actor version. """

        try:
            dev = self.device(channel)
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return
        cmd.inform(f'text="dev={dev} {dev.sendOneCommand}"')
        ret = dev.sendOneCommand(cmdStr=cmd.cmd.keywords['raw'].values[0],
                                 cmd=cmd)

        cmd.inform('text="returned %s"' % (ret))
        cmd.finish()

    def raw(self, cmd):
        """Report camera status and actor version. """

        self._raw(cmd, channel=1)

    def raw2(self, cmd):
        """Report camera status and actor version. """

        self._raw(cmd, channel=2)

    def _init(self, cmd, dev, channel=None):
        cmdList = ['*RST',
                   'SENS1:CURR:NPLC 1',
                   'SYST:AZER OFF']

        if channel is None:
            cmdList.extend(
                    ['SOUR1:GCON ON',
                     'SOUR2:GCON ON',
                     'SOUR1:VOLT:MODE FIX',
                     'SOUR2:VOLT:MODE FIX',
                     'SOUR1:VOLT:RANG 10',
                     'SOUR2:VOLT:RANG 10',
                     'SOUR1:VOLT 0',
                     'SOUR2:VOLT 0',
                     'OUTP1 OFF',
                     'OUTP2 OFF',
                     'SENS1:CURR:RANG:AUTO ON',
                     'SENS2:CURR:RANG:AUTO ON'])

        elif channel == 1:
            cmdList.extend(
                    ['SOUR1:GCON ON',
                     'SOUR1:VOLT:MODE FIX',
                     'SOUR1:VOLT:RANG 10',
                     'SOUR1:VOLT 0',
                     'OUTP1 OFF',
                     'SENS1:CURR:RANG:AUTO ON'])
        else:
            cmdList.extend(
                    ['SYST:ZCH OFF',
                     'SYST:ZCOR OFF',
                     'SOUR1:VOLT:MODE FIX',
                     'SOUR1:VOLT:RANG 10',
                     'SOUR1:VOLT 0',
                     'OUTP1 OFF',
                    'SENS1:CURR:RANG:AUTO ON'])

        for c in cmdList:
            dev.sendOneCommand(c, cmd=cmd, noResponse=True)
        cmd.finish()

    def init(self, cmd):
        try:
            dev = self.keithley
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return
        self._init(cmd, dev)

    def init2(self, cmd):
        try:
            dev = self.keithley2
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return
        self._init(cmd, dev, channel=2)

    def _read(self, cmd, channel):
        """Take a single reading. """
        cmdKeys = cmd.cmd.keywords

        meas = self.current(channel=channel, cmd=cmd)
        cmd.inform(f'text="chan {channel}: {meas}"')

    def read(self, cmd):
        """Take a single reading. """
        cmdKeys = cmd.cmd.keywords
        if 'chan' in cmdKeys:
            chan = int(cmdKeys['chan'].values[0])
            if chan not in {1,2}:
                cmd.fail('text="chan must be 1 or 2')
                return
            chans = [chan]
        else:
            chans = [1,2]

        for chan in chans:
            self._read(cmd, channel=chan)
        cmd.finish()

    def n8pds(self, cmd):
        """Take and store a """
        cmdKeys = cmd.cmd.keywords
        wave = cmdKeys['wave'].values[0] if 'wave' in cmdKeys else -9999
        power = cmdKeys['power'].values[0] if 'power' in cmdKeys else -9999
        nread = cmdKeys['nread'].values[0]  if 'nread' in cmdKeys else 9
        name = cmdKeys['name'].values[0]
        note = cmdKeys['note'].values[0] if 'note' in cmdKeys else ''
        note = note.replace(' ', '_')

        dfRows = []
        meas = self.allCurrents(cmd=cmd, number_keithley_reads=nread)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        for c in range(2):
            cmd.inform(f'text="chan {c+1}: {np.median(meas[:,c])}"')
        for m_i, m in enumerate(meas):
            dfRows.append(dict(ts=ts, name=name, wavelength=wave, power=power,
                                reading=m_i, chan1=m[0], chan2=m[1],
                                note=note))
        df = pd.DataFrame(dfRows)
        fname = f'/data/pfseng/n8_photodiode/pdmeas2_{name}_{ts}.txt'
        with open(fname, 'at') as f:
            f.write(df.to_string() + '\n')
        cmd.finish(f'text="wrote {fname}"')

    def n8pds2(self, cmd):
        """Take and store a """
        cmdKeys = cmd.cmd.keywords
        wave = cmdKeys['wave'].values[0] if 'wave' in cmdKeys else -9999
        power = cmdKeys['power'].values[0] if 'power' in cmdKeys else -9999
        nread = cmdKeys['nread'].values[0] if 'nread' in cmdKeys else 9
        name = cmdKeys['name'].values[0]
        note = cmdKeys['note'].values[0] if 'note' in cmdKeys else ''
        note = note.replace(' ', '_')

        self.fireBoth(number_keithey_reads=nread, cmd=cmd)

        meas1 = self.readOne(1, cmd=cmd)
        meas2 = self.readOne(2, cmd=cmd)
        meas = np.stack([meas1, meas2], axis=1)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        for c in range(2):
            cmd.inform(f'text="chan {c+1}: {np.median(meas[:,c])}"')

        dfRows = []
        for m_i, m in enumerate(meas):
            dfRows.append(dict(ts=ts, name=name, wavelength=wave, power=power,
                               reading=m_i, chan1=m[0], chan2=m[1],
                               note=note))
        df = pd.DataFrame(dfRows)
        fname = f'/data/pfseng/n8_photodiode/pdmeas2_{name}_{ts}.txt'
        with open(fname, 'at') as f:
            f.write(df.to_string() + '\n')
        cmd.finish(f'text="wrote {fname}"')

    def fireOne(self, channel, number_keithley_reads=7, cmd=None):
        try:
            dev = self.device(channel)
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        if channel == 1:
            FORMcmd = 'FORM:ELEM:TRAC CURR%s' % str(channel)
        else:
            FORMcmd = 'FORM:ELEM READ'

        cmds = ('TRAC:POIN %2i' % number_keithley_reads,
                'TRAC:FEED:CONT NEXT',
                'TRIG:COUN %2i' % number_keithley_reads,
                FORMcmd,
                'INIT')

        for c in cmds:
            ret = dev.sendOneCommand(cmdStr=c, cmd=cmd, noResponse=True)

    def readOne(self, channel, cmd=None):
        try:
            dev = self.device(channel)
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        readCmd = 'TRACE:DATA?'
        ret = dev.sendOneCommand(cmdStr=readCmd, cmd=cmd)
        rawArray = np.fromstring(ret, sep=',')
        data_current_split = rawArray

        return data_current_split

    def fireBoth(self, number_keithey_reads=7, cmd=None):
        for chan in 1,2:
            self.fireOne(chan, number_keithley_reads=number_keithey_reads, cmd=cmd)

    def current(self, channel, current_number=1, number_keithley_reads=7, cmd=None):
        try:
            dev = self.device(channel)
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        if channel == 1:
            FORMcmd = 'FORM:ELEM:TRAC CURR%s' % str(current_number)
        else:
            FORMcmd = 'FORM:ELEM READ'

        cmds = ('TRAC:POIN %2i' % number_keithley_reads,
                'TRAC:FEED:CONT NEXT',
                'TRIG:COUN %2i' % number_keithley_reads,
                FORMcmd,
                'INIT')

        for c in cmds:
            ret = dev.sendOneCommand(cmdStr=c, cmd=cmd, noResponse=True)

        readCmd = 'TRACE:DATA?'
        ret = dev.sendOneCommand(cmdStr=readCmd, cmd=cmd)
        data_current_split = tuple(map(float, ret.split(',')))

        rawArray = np.fromstring(ret, sep=',')
        data_current_split = rawArray

        return data_current_split

    def allCurrents(self, number_keithley_reads=7, cmd=None):
        try:
            dev = self.keithley
        except Exception as e:
            cmd.fail('text="not connected! (%s)"' % (e))
            return

        cmds = ('TRAC:POIN %2i' % number_keithley_reads,
                'TRAC:FEED:CONT NEXT',
                'TRIG:COUN %2i' % number_keithley_reads,
                'FORM:ELEM:TRAC CURR1,CURR2',
                'INIT')
        for c in cmds:
            ret = dev.sendOneCommand(c, cmd=cmd, noResponse=True)

        readCmd = 'TRACE:DATA?'
        ret = dev.sendOneCommand(readCmd, cmd=cmd)

        rawArray = np.fromstring(ret, sep=',')
        data_current_split = rawArray.reshape(number_keithley_reads, 2)

        return data_current_split



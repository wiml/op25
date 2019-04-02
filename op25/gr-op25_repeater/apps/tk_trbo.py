# MotoTRBO trunking module
#
# Copyright 2019 Graham J. Norbury - gnorbury@bondcar.com
# 
# This file is part of OP25
# 
# OP25 is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# OP25 is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with OP25; see the file COPYING. If not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Boston, MA
# 02110-1301, USA.
#

import sys
import time
import json

CC_HUNT_TIMEOUTS = 3

class dmr_chan:
    def __init__(self, debug=0, lcn=0, freq=0):
        self.debug = debug
        self.lcn = lcn
        self.frequency = freq

class dmr_receiver:
    def __init__(self, msgq_id, frequency_set=None, chans={}, debug=0):
        class _states(object):
            IDLE = 0
            CC   = 1
            VC   = 2
            SRCH = 3
        self.trbo_type = -1
        self.states = _states
        self.current_state = self.states.IDLE
        self.frequency_set = frequency_set
        self.msgq_id = msgq_id
        self.debug = debug
        self.cc_timeouts = 0
        self.chans = chans
        self.chan_list = self.chans.keys()
        self.current_chan = 0
        self.rest_lcn = 0

    def find_freq(self, lcn):
        if self.chans.has_key(lcn):
            return self.chans[lcn].frequency
        else:
            return (None, None)

    def find_next_chan(self, current_chan):
        num_chans = len(self.chan_list)
        next_chan = current_chan + 1
        if next_chan >= num_chans:
            next_chan = 0
        return next_chan

    def process_qmsg(self, msg):
        if msg.arg2() != 1: # discard anything not DMR
            return

        m_type = int(msg.type())
        m_slot = int(msg.arg1()) & 0x1
        m_proto = int(msg.arg2())
        m_buf = msg.to_string()

        if m_type == -1:  # Sync Timeout
            if self.msgq_id == 0:
                self.cc_timeouts += 1

                if self.cc_timeouts >= CC_HUNT_TIMEOUTS:
                    if self.debug >= 1:
                        sys.stderr.write("%f [%d] Searching for control channel\n" % (time.time(), self.msgq_id))
                    self.cc_timeouts = 0
                    next_ch = self.find_next_chan(self.current_chan)
                    self.frequency_set({'tuner': 'trunk',
                                        'freq': self.chans[self.chan_list[next_ch]].frequency,
                                        'slot': 0})
                    self.current_chan = next_ch
            else:
                pass
            return
        elif m_type >= 0: # Receiving a PDU means sync must be present
            if self.msgq_id == 0:
                self.cc_timeouts = 0

        # log received message
        if self.debug >= 9:
            d_buf = "0x"
            for byte in m_buf:
                d_buf += format(ord(byte),"02x")
            sys.stderr.write("%f [%d] DMR PDU: type(%d), slot(%d), data(%s)\n" % (time.time(), self.msgq_id, m_type, m_slot, d_buf))

	if m_type == 0: # CACH SLC
            self.rx_CACH_SLC(m_buf)
        elif m_type == 1: # CACH CSBK
            pass
        elif m_type == 2: # SLOT PI
            pass
        elif m_type == 3: # SLOT VLC
            pass
        elif m_type == 4: # SLOT TLC
            pass
        elif m_type == 5: # SLOT CSBK
            self.rx_SLOT_CSBK(m_buf)
        elif m_type == 6: # SLOT MBC
            pass
        elif m_type == 7: # SLOT ELC
            pass
        elif m_type == 8: # SLOT ERC
            pass
        elif m_type == 9: # SLOT ESB
            pass
        else:             # Unknown Message
            return

    def rx_CACH_SLC(self, m_buf):
        slco = ord(m_buf[0])
        d0 = ord(m_buf[1])
        d1 = ord(m_buf[2])
        d2 = ord(m_buf[3])

        if slco == 0:    # Null Msg (Idle Channel)
            if self.debug >= 9:
                sys.stderr.write("%f [%d] SLCO NULL MSG\n" % (time.time(), self.msgq_id))
        elif slco == 1:  # Act Update
                ts1_act = d0 >> 4;
                ts2_act = d0 & 0xf;
                if self.debug >= 9:
                    sys.stderr.write("%f [%d] ACTIVITY UPDATE TS1(%x), TS2(%x), HASH1(%02x), HASH2(%02x)\n" % (time.time(), self.msgq_id, ts1_act, ts2_act, d1, d2))
        elif slco == 9:  # Connect Plus Voice Channel
            netId = (d0 << 4) + (d1 >> 4)
            siteId = ((d1 & 0xf) << 4) + (d2 >> 4)
            if self.trbo_type < 0:
                self.trbo_type = 1
                sys.stderr.write("%f [%d] TRBO_TYPE SET TO CONNECT PLUS\n" % (time.time(), self.msgq_id))
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CONNECT PLUS VOICE CHANNEL: netId(%d), siteId(%d)\n" % (time.time(), self.msgq_id, netId, siteId))
        elif slco == 10: # Connect Plus Control Channel
            netId = (d0 << 4) + (d1 >> 4)
            siteId = ((d1 & 0xf) << 4) + (d2 >> 4)
            if self.trbo_type < 0:
                self.trbo_type = 1
                sys.stderr.write("%f [%d] TRBO_TYPE SET TO CONNECT PLUS\n" % (time.time(), self.msgq_id))
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CONNECT PLUS CONTROL CHANNEL: netId(%d), siteId(%d)\n" % (time.time(), self.msgq_id, netId, siteId))
        elif slco == 15: # Capacity Plus Channel
            lcn = d1
            if self.trbo_type < 0:
                self.trbo_type = 0
                sys.stderr.write("%f [%d] TRBO_TYPE SET TO CAPACITY PLUS\n" % (time.time(), self.msgq_id))
            self.rest_lcn = d1
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CAPACITY PLUS REST CHANNEL: lcn(%d)\n" % (time.time(), self.msgq_id, lcn))
        else:
            if self.debug >= 9:
                sys.stderr.write("%f [%d] UNKNOWN CACH SLCO(%d)\n" % (time.time(), self.msgq_id, slco))
            return

    def rx_SLOT_CSBK(self, m_buf):
        op  = ord(m_buf[0]) & 0x3f
        fid = ord(m_buf[1])

        if (op == 1) and (fid == 6):     # ConnectPlus Neighbors
            nb1 = ord(m_buf[2]) & 0x3f
            nb2 = ord(m_buf[3]) & 0x3f
            nb3 = ord(m_buf[4]) & 0x3f
            nb4 = ord(m_buf[5]) & 0x3f
            nb5 = ord(m_buf[6]) & 0x3f
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CONNECT PLUS NEIGHBOR SITES: %d, %d, %d, %d, %d\n" % (time.time(), self.msgq_id, nb1, nb2, nb3, nb4, nb5))
        elif (op == 3) and (fid == 6):   # ConnectPlus Channel Grant
            src_addr = (ord(m_buf[2]) << 16) + (ord(m_buf[3]) << 8) + ord(m_buf[4])
            grp_addr = (ord(m_buf[5]) << 16) + (ord(m_buf[6]) << 8) + ord(m_buf[7])
            lcn      = (ord(m_buf[8]) >> 4)
            slot     = (ord(m_buf[8]) >> 5) & 0x1 
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CONNECT PLUS CHANNEL GRANT: grpAddr(%06x), srcAddr(%06x), lcn(%d), slot(%d)\n" % (time.time(), self.msgq_id, grp_addr, src_addr, lcn, slot))

            freq = self.find_freq(lcn)
            if freq is not None:
                self.frequency_set({'tuner': 'voice',
                                    'freq': freq,
                                    'slot': slot})

        elif (op == 59) and (fid == 16): # CapacityPlus Sys/Sites/TS
            fl   =  (ord(m_buf[2]) >> 6)
            ts   = ((ord(m_buf[2]) >> 5) & 0x1)
            rest =  (ord(m_buf[2]) & 0x1f)
            bcn  = ((ord(m_buf[3]) >> 7) & 0x1)
            site = ((ord(m_buf[3]) >> 3) & 0xf)
            nn   =  (ord(m_buf[3]) & 0x7)
            if nn > 6:
                nn = 6
            if self.debug >= 9:
                sys.stderr.write("%f [%d] CAPACITY PLUS SYSSITES: rest(%d), beacon(%d), siteId(%d), nn(%d)\n" % (time.time(), self.msgq_id, rest, bcn, site, nn))
            
        elif (op == 62):                 # 
            pass

class rx_ctl(object):
    def __init__(self, debug=0, frequency_set=None, chans=None):
        self.frequency_set = frequency_set
        self.debug = debug
        self.receivers = {}

        self.chans = {}
        for _chan in chans:
            self.chans[_chan['lcn']] = dmr_chan(debug, _chan['lcn'], _chan['frequency'])
            sys.stderr.write("%f Configuring channel lcn(%d), freq(%f), cc(%d)\n" % (time.time(), _chan['lcn'], (_chan['frequency']/1e6), _chan['cc']))

    def add_receiver(self, msgq_id):
        self.receivers[msgq_id] = dmr_receiver(msgq_id, self.frequency_set, self.chans, self.debug)

    def process_qmsg(self, msg):
        if msg.arg2() != 1: # discard anything not DMR
            return

        m_rxid = int(msg.arg1()) >> 1
        if self.receivers.has_key(m_rxid):
            self.receivers[m_rxid].process_qmsg(msg)

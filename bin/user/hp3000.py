#!/usr/bin/env python
# Copyright 2016 Matthew Wall
# Distributed under the terms of the GNU Public License (GPLv3)

"""
Collect data from the HP-3000 console via USB.

  Ambient Weather WS-3000-X5
  Ambient Weather WS-3000-X3

The HP-3000 supports up to 8 remote temperature/humidity sensors.  The console
has a 3"x4" TFT color display, with graph and room for 5 sensor displays.  The
sensor display regions can cycle through different sensors when more than 5
sensors are connected.

Every configuration option in the console can be modified via software.  These
options includes:

 - archive interval
 - date/time
 - date/time format
 - timezone
 - which sensors should be displayed in the 5 display regions
 - horizontal graph axis scaling
 - vertical graph axis
 - calibration for temperature/humidity from each sensor
 - alarms
 - historical data

Historical data are saved to the (optional) microSD card.  If no card is
installed, no data are retained.

Each sensor has its own display of temperature and humidity.

Each sensor is identified by channel number.  The channel number is set using
DIP switches on each sensor.  The DIP switches also determine which units will
be displayed in each sensor.

There are 4 two-position DIP switches.  DIP 4 determines units: 0=F 1=C
DIP 1-3 determine which of 8 channels is selected.

Each sensor uses 2 AA batteries.  Nominal battery life is 1 year.

The console uses 5V DC from an AC/DC transformer.

Data from sensors are received every 60 seconds.

Dewpoint and heatindex are calculated within the console.

Temperature sensors measure to +/- 2 degree F

Humidity sensors measure to +/- 5 %

Calibrations are applied in the console, so the values received from the
console are calibrated.  Calculations in the console are performed in degree C.

The console has a radio controlled clock.  During RCC reception, no data will
be transmitted.  If no RCC is received, attempt will be made every two hours
until successful.

This driver was developed without any assistance from Ambient Weather (the
vendor) or Fine Offset (the manufacturer).

===============================================================================
Messages from console

The console sends data in 64-byte chunks.  It looks like the console reuses a
buffer, because each message shorter than the previous contains bytes from the
previous message.  The byte sequence 0x40 0x7d indicates end of data within a
buffer.

Many of the console messages correspond with the control messages sent from
the host.

configuration state (30 bytes)
00 7b
01 00 graph type
02 48 graph hours
03 01 time format
04 00 date format
05 00 dst
06 fb timezone
07 01 units
08 00
09 00
0a 00
0b 07 area1
0c 00
0d 00
0e 00
0f 00 area2
10 00
11 00
12 00
13 00 area3
14 00
15 00
16 00
17 00 area4
18 00
19 00
1a 00
1b 00 area5
1c 40
1d 7d

interval (4 bytes)
00 7b
01 05 interval in minutes
02 40
03 7d

unknown (9 bytes)
00 7b
01 01
02 01
03 00
04 00
05 00
06 00
07 40
08 7d

current data (27 bytes)
00 7b
01 00 ch1 temp MSB
02 eb ch1 temp LSB    t1 = (MSB * 256 + LSB) / 10.0
03 25 ch1 hum         h1 = hum
04 7f ch2 temp MSB
05 ff ch2 temp LSB
06 ff ch2 hum
07 7f ch3 temp MSB
08 ff ch3 temp LSB
09 ff ch3 hum
0a 7f ch4 temp MSB
0b ff ch4 temp LSB
0c ff ch4 hum
0d 7f ch5 temp MSB
0e ff ch5 temp LSB
0f ff ch5 hum
10 7f ch6 temp MSB
11 ff ch6 temp LSB
12 ff ch6 hum
13 7f ch7 temp MSB
14 ff ch7 temp LSB
15 ff ch7 hum
16 7f ch8 temp MSB
17 ff ch8 temp LSB
18 ff ch8 hum
19 40
1a 7d

calibration (27 bytes)
00 7b
01 00 ch1 temp MSB
02 00 ch1 temp LSB    tcal1 = (MSB * 256 + LSB) / 10.0
03 00 ch1 hum         hcal1 = hum
04 00 ch2 temp MSB
05 00 ch2 temp LSB
06 00 ch2 hum
07 00 ch3 temp MSB
08 00 ch3 temp LSB
09 00 ch3 hum
0a 00 ch4 temp MSB
0b 00 ch4 temp LSB
0c 00 ch4 hum
0d 00 ch5 temp MSB
0e 00 ch5 temp LSB
0f 00 ch5 hum
10 00 ch6 temp MSB
11 00 ch6 temp LSB
12 00 ch6 hum
13 00 ch7 temp MSB
14 00 ch7 temp LSB
15 00 ch7 hum
16 00 ch8 temp MSB
17 00 ch8 temp LSB
18 00 ch8 hum
19 40
1a 7d

humidity alarm configuration (19 bytes)
00 7b
01 5a ch1 hi    0x5a = 90 %
02 14 ch1 lo    0x14 = 20 %
03 5a ch2 hi
04 14 ch2 lo
05 5a ch3 hi
06 14 ch3 lo
07 5a ch4 hi
08 14 ch4 lo
09 5a ch5 hi
0a 14 ch5 lo
0b 5a ch6 hi
0c 14 ch6 lo
0d 5a ch7 hi
0e 14 ch7 lo
0f 5a ch8 hi
10 14 ch8 lo
1a 40
1b 7d

temperature alarm configuration (35 bytes)
00 7b
01 01 ch1 hi  (0x01*256 + 0x2c) / 10.0 = 30.0 C
02 2c
03 00 ch1 lo  (0x00*256 + 0x64) / 10.0 = 10.0 C
04 64
05 01 ch2 hi
06 2c
07 00 ch2 lo
08 64
09 01 ch3 hi
0a 2c
0b 00 ch3 lo
0c 64
0d 01 ch4 hi
0e 2c
0f 00 ch4 lo
10 64
11 01 ch5 hi
12 2c
13 00 ch5 lo
14 64
15 01 ch6 hi
16 2c
17 00 ch6 lo
18 64
19 01 ch7 hi
1a 2c
1b 00 ch7 lo
1c 64
1d 01 ch8 hi
1e 2c
1f 00 ch8 lo
20 64
21 40
22 7d

===============================================================================
Messages to console

Each command buffer is terminated by the bytes 0x40 0x7d.

The host sends a sequence of what appear to be empty commands, approximately
every 30 seconds:

7b 06 40 7d
7b 08 40 7d
7b 09 40 7d
7b 05 40 7d
7b 03 40 7d
7b 04 40 7d
7b 41 40 7d

Other commands are sent when a specific action is performed in the software:

set configuration command (0x10)
00 7b
01 10
02 00 graph type  0=temperature 1=humidity 2=dewpoint 3=heatindex
03 48 graph hours 0x0c=12H 0x18=24H 0x30=48H 48=72H
04 00 time format 0='h:mm:ss' 1='am h:mm:ss' 2='h:mm:ss am'
05 00 date format 0='dd-mm-yyyy' 1='mm-dd-yyyy' 2='yyyy-mm-dd'
06 00 dst         0=off 1=on
07 fb timezone    0xNN - 0x100 if (0xNN & 0xf0 == 0xf0) else 0xNN
08 00 units       1=F 0=C
09 00
0a 00
0b 00
0c 07 area1 01=temp 02=dew 03=temp/dew 07=temp/dew/heat
0d 00
0e 00
0f 00
10 08 area2 08=temp 20=heat 38=temp/dew/heat  (3f=1+2=temp/dew/heat ?)
11 00
12 00
13 00
14 00 area3?
15 00
16 00
17 00
18 00 area4?
19 00
1a 00
1b 00
1c 00 area5?
1d 40
1e 7d

set calibration command (0x11)
00 7b
01 11
02 00
03 0a ch1.T  t*10
04 00 ch1.H
05 00
06 14 ch2.T  t*10
07 00 ch2.H
08 00
09 00 ch3.T
0a 00 ch3.H
0b 00
0c 00 ch4.T
0d 00 ch4.H
0e 00
0f 32 ch5.T  t*10
10 00 ch5.H
11 00
12 00 ch6.T
13 00 ch6.H
14 00
15 00 ch7.T
16 00 ch7.H
17 00
18 00 ch8.T
19 00 ch8.H
1a 40
1b 7d

sync time command (0x30)
00 7b
01 30
02 07 year MSB
03 e0 year LSB
04 0c month
05 11 day-of-month
06 00 hour
07 27 minute
08 0c second?
09 06
0a 40
0b 7d

set interval command (0x40)
00 7b
01 40
02 05 interval in minutes (5-240)
03 40
04 7d

"""

# FIXME: set backlight (enable/disable; on time; off time)
# FIXME: re-register sensors
# FIXME: set alarms (temp on/off; hum on/off; hi/lo temps; hi/lo hums)
# FIXME: clear min/max
# FIXME: get min/max values
# FIXME: verify encoding of negative temperature values
# FIXME: verify encoding of negative timezone offsets

from __future__ import with_statement
import Queue
import syslog
import time

import weeusb
import weewx.drivers

DRIVER_NAME = 'HP3000'
DRIVER_VERSION = '0.3'

def loader(config_dict, _):
    return HP3000Driver(**config_dict[DRIVER_NAME])

def confeditor_loader():
    return HP3000ConfigurationEditor()


def logmsg(level, msg):
    syslog.syslog(level, 'hp3000: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)


def _fmt(buf):
    if buf:
        return "%s (len=%s)" % (' '.join(["%02x" % x for x in buf]), len(buf))
    return ''


class HP3000ConfigurationEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[HP3000]
    # This section is for HP-3000 temperature/humidity sensors

    # The model name such as Ambient WS-3000-X5
    model = WS-3000

    # The driver to use
    driver = user.hp3000
"""


class HP3000Driver(weewx.drivers.AbstractDevice):

    DEFAULT_MAP = {
        'inTemp': 't_1',
        'inHumidity': 'h_1',
        'outTemp': 't_2',
        'outHumidity': 'h_2',
        'extraTemp1': 't_3',
        'extraHumid1': 'h_3',
        'extraTemp2': 't_4',
        'extraHumid2': 'h_4',
        'extraTemp3': 't_5',
        'extraHumid3': 'h_5',
        'extraTemp4': 't_6',
        'extraHumid4': 'h_6',
        'extraTemp5': 't_7',
        'extraHumid5': 'h_7',
        'extraTemp6': 't_8',
        'extraHumid6': 'h_8'}

    def __init__(self, **stn_dict):
        loginf('driver version is %s' % DRIVER_VERSION)
        loginf('usb info: %s' % weeusb.USBHID.get_usb_info())
        self._model = stn_dict.get('model', 'HP3000')
        self._max_tries = int(stn_dict.get('max_tries', 5))
        self._retry_wait = int(stn_dict.get('retry_wait', 3))
        self._ping_interval = int(stn_dict.get('ping_interval', 30))
        self._sensor_map = dict(HP3000Driver.DEFAULT_MAP)
        if 'sensor_map' in stn_dict:
            self._sensor_map.update(stn_dict['sensor_map'])
        loginf('sensor map: %s' % self._sensor_map)
        self._station = HP3000Station()
        self._station.open()

    def closePort(self):
        self._station.close()

    def hardware_name(self):
        return self._model

    def genLoopPackets(self):
        cnt = 0
        last_send = 0
        while cnt < self._max_tries:
            cnt += 1
            try:
                now = time.time()
                if now - last_send > self._ping_interval:
                    self._station.send_sequence()
                    last_send = now
                raw = self._station.recv()
                cnt = 0
                data = HP3000Station.raw_to_pkt(raw)
                logdbg('data: %s' % data)
                if data and data.get('type') == 'sensor_values':
                    pkt = self._data_to_packet(data)
                    logdbg('packet: %s' % pkt)
                    yield pkt
                time.sleep(1)
            except weewx.WeeWxIOError, e:
                loginf("Failed attempt %d of %d: %s" %
                       (cnt, self._max_tries, e))
                logdbg("Waiting %d seconds before retry" % self._retry_wait)
                time.sleep(self._retry_wait)
        else:
            msg = "Max retries (%d) exceeded" % self._max_tries
            logerr(msg)
            raise weewx.RetriesExceeded(msg)

    def _data_to_packet(self, data):
        # map sensor data to database fields
        pkt = {'dateTime': int(time.time() + 0.5), 'usUnits': weewx.METRICWX}
        for x in self._sensor_map:
            if self._sensor_map[x] in data:
                pkt[x] = data[self._sensor_map[x]]
        return pkt


class HP3000Station(weeusb.USBHID):
    # usb values obtained from 'sudo lsusb -v'
    USB_ENDPOINT_IN = 0x82
    USB_ENDPOINT_OUT = 0x02
    USB_PACKET_SIZE = 0x40 # 64 bytes

    def __init__(self):
        super(HP3000Station, self).__init__(0x0483, 0x5750)

    def write(self, buf):
        logdbg("write: %s" % _fmt(buf))
        return self._write(buf)

    def read(self, timeout=100):
        buf = self._read(self.USB_PACKET_SIZE, self.USB_ENDPOINT_IN, timeout)
        if not buf:
            return None
        logdbg("read: %s" % _fmt(buf))
        if len(buf) != 64:
            raise weewx.WeeWxIOError('read: bad buffer length: '
                                     '%s != 64' % len(buf))
        if buf[0] != 0x7b:
            raise weewx.WeeWxIOError('read: bad first byte: '
                                     '0x%02x != 0x7b' % buf[0])
        idx = None
        try:
            i = buf.index(0x40)
            if buf[i + 1] == 0x7d:
                idx = i
        except ValueError, IndexError:
            pass
        if idx is None:
            raise weewx.WeeWxIOError('read: no terminating bytes in buffer: '
                                     '%s' % _fmt(buf))
        return buf[0: idx + 2]

    def send_cmd(self, cmd):
        self.write([0x7b, cmd, 0x40, 0x7d])

    def send_sequence(self):
        self.send_cmd(0x06)
        self.send_cmd(0x08)
        self.send_cmd(0x09)
        self.send_cmd(0x05)
        self.send_cmd(0x03)
        self.send_cmd(0x04)
        self.send_cmd(0x41)

    def recv(self):
        return self.read(timeout=100)

    GRAPH_TYPE = {
        0: 'temperature',
        1: 'humidity',
        2: 'dewpoint',
        3: 'heatindex'}
    TIME_FORMAT = {
        0: 'h:mm:ss',
        1: 'AM h:mm:ss',
        2: 'h:mm:ss AM'}
    DATE_FORMAT = {
        0: 'dd-mm-yyyy',
        1: 'mm-dd-yyyy',
        2: 'yyyy-mm-dd'}
    DST = {
        0: 'off',
        1: 'on'}
    UNITS = {
        0: 'degree_C',
        1: 'degree_F'}

    @staticmethod
    def decode_timezone(x):
        if (x & 0xf0) == 0xf0:
            return x - 0x100
        return x

    @staticmethod
    def raw_to_pkt(buf):
        logdbg("raw: %s" % _fmt(buf))
        pkt = dict()
        if not buf:
            return pkt
        if len(buf) == 4: # archive interval
            pkt['type'] = 'interval'
            pkt['interval'] = buf[1]
        elif len(buf) == 30: # configuration
            pkt['type'] = 'configuration'
            pkt['graph_type'] = HP3000Station.GRAPH_TYPE.get(buf[1])
            pkt['graph_hours'] = buf[2]
            pkt['time_format'] = HP3000Station.TIME_FORMAT.get(buf[3])
            pkt['date_format'] = HP3000Station.DATE_FORMAT.get(buf[4])
            pkt['dst'] = HP3000Station.DST.get(buf[5])
            pkt['timezone'] = HP3000Station.decode_timezone(buf[6])
            pkt['units'] = HP3000Station.UNITS.get(buf[7])
            pkt['area1'] = buf[11]
            pkt['area2'] = buf[15]
            pkt['area3'] = buf[19]
            pkt['area4'] = buf[23]
            pkt['area5'] = buf[27]
        elif len(buf) == 19: # humidity alarm
            pkt['type'] = 'alarm_humidity'
            for ch in range(8):
                idx = 1 + ch * 2
                pkt['hhi_%s' % (ch + 1)] = buf[idx]
                pkt['hlo_%s' % (ch + 1)] = buf[idx + 1]
        elif len(buf) == 35: # temperature alarm
            pkt['type'] = 'alarm_temperature'
            for ch in range(8):
                idx = 1 + ch * 4
                pkt['thi_%s' % (ch + 1)] = (buf[idx] * 256 + buf[idx + 1]) / 10.0
                pkt['tlo_%s' % (ch + 1)] = (buf[idx + 2] * 256 + buf[idx + 3]) / 10.0
        elif len(buf) == 27: # sensor values or sensor calibration
            # there is no way to distinguish between calibration and values.
            # so we assume that none of the sensors have been calibrationed;
            # a buffer with all zeros must thus be a calibration packet.
            if buf[1: -2] == [0] * 24:
                pkt['type'] = 'sensor_calibration'
                for ch in range(8):
                    idx = 1 + ch * 3
                    pkt['tc_%s' % (ch + 1)] = (buf[idx] * 256 + buf[idx + 1]) / 10.0
                    pkt['hc_%s' % (ch + 1)] = buf[idx + 2]
            else:
                pkt['type'] = 'sensor_values'
                for ch in range(8):
                    idx = 1 + ch * 3
                    if buf[idx] != 0x7f and buf[idx + 1] != 0xff:
                        pkt['t_%s' % (ch + 1)] = (buf[idx] * 256 + buf[idx + 1]) / 10.0
                    if buf[idx + 2] != 0xff:
                        pkt['h_%s' % (ch + 1)] = buf[idx + 2]
        else:
            logdbg("unknown data: %s" % _fmt(buf))
        return pkt


# define a main entry point for basic testing of the station.  invoke this as
# follows from the weewx root dir:
#
# PYTHONPATH=bin python bin/user/hp3000.py

if __name__ == '__main__':

    import optparse

    usage = """%prog [options] [--debug] [--help]"""

    syslog.openlog('hp3000', syslog.LOG_PID | syslog.LOG_CONS)
    syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_INFO))
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', action='store_true',
                      help='display driver version')
    parser.add_option('--debug', action='store_true',
                      help='display diagnostic information while running')
    parser.add_option('--test', default='station',
                      help='what to test: station or driver')
    (options, args) = parser.parse_args()

    if options.version:
        print "driver version %s" % DRIVER_VERSION
        exit(1)

    if options.debug:
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    if options.test == 'driver':
        driver = HP3000Driver()
        try:
            for p in driver.genLoopPackets():
                print p
        finally:
            driver.closePort()
    else:
        with HP3000Station() as s:
            last_ping = 0
            while True:
                try:
                    now = time.time()
                    if now - last_ping > 30:
                        s.send_sequence()
                        last_ping = now
                    raw = s.recv()
                    print "raw: %s" % _fmt(raw)
                    pkt = HP3000Station.raw_to_pkt(raw)
                    print "pkt: %s" % pkt
                except weewx.WeeWxIOError, e:
                    print "fail: %s" % e
                time.sleep(1)

#!/usr/bin/env python3

"""This is a test program for testing the code out on the host."""

import os
import struct
import sys
from bus import Bus, BusError
from log import log

class Scanner(object):

    def __init__(self, bus, start_id=1, num_ids=32):
        self.scan_idx = 0
        self.scan_spin = "-\\|/"
        self.ids = []
        bus.scan(start_id, num_ids, self.dev_found, None)

    def dev_found(self, bus, dev_id):
        # We want to read the model and version, which is at offset 0, 1,
        # and 2 so we do it with a single read.
        try:
            data = bus.read(dev_id, 0, 3)
        except BusError:
            log('Device {} READ timed out'.format(dev_id))
            return
        model, version = struct.unpack('<HB', data)
        print('ID: {:3d} Model: {:5d} Version: {:5d}'.format(dev_id, model, version))
        self.ids.append(dev_id)


def scan(bus):
    print('Scanning IDs 0-32...')
    scanner = Scanner(bus, 0, 32)
    if len(scanner.ids) == 0:
        print('No bioloid servos detected')
    scanner2 = Scanner(bus, 100, 32)
    if len(scanner2.ids) == 0:
        print('No bioloid sensors detected')

def pyboard_main():
    from stm_uart_bus import UART_Bus
    serial = UART_Bus(2, 1000000)
    bus = Bus(serial, show_packets=False)
    scan(bus)


def linux_main():
    import argparse

    default_baud = 1000000
    default_port = os.getenv("BIOLOID_PORT") or '/dev/ttyUSB0'
    parser = argparse.ArgumentParser(
        prog="test",
        usage="%(prog)s [options] [command]",
        description="Send commands to bioloid devices",
        epilog=("You can specify the default serial port using the " +
                "BIOLOID_PORT environment variable.")
    )
    parser.add_argument(
        "-b", "--baud",
        dest="baud",
        action="store",
        type=int,
        help="Set the baudrate used (default = %d)" % default_baud,
        default=default_baud
    )
    default_port_help = ""
    if default_port:
        default_port_help = " (default '%s')" % default_port
    parser.add_argument(
        "-p", "--port",
        dest="port",
        help="Set the serial port to use" + default_port_help,
        default=default_port
    )
    parser.add_argument(
        "-n", "--net",
        dest="net",
        action="store_true",
        help="Connect to a device using TCP/IP",
        default=False
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        action="store_true",
        help="Turn on verbose messages",
        default=False
    )
    parser.add_argument(
        "--dummy",
        dest="dummy",
        action="store_true",
        help="Uses DummyPort",
        default=False
    )
    args = parser.parse_args(sys.argv[1:])

    show_packets = args.verbose
    if args.dummy:
        from dummy_port import DummyPort
        dev_port = DummyPort()
        show_packets = True
    elif args.net:
        import socket
        from socket_port import SocketPort

        IP_ADDR = '127.0.0.1'
        IP_PORT = 8888
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP_ADDR, IP_PORT))
        dev_port = SocketPort(s)
    else:
        import serial
        from serial_port import SerialPort
        try:
            dev_port = SerialPort(args.port, args.baud)
        except serial.serialutil.SerialException:
            print("Unable to open port '{}'".format(port))
            sys.exit()
    bus = Bus(dev_port, show_packets=show_packets)
    scan(bus)


def main():
    sysname = os.uname().sysname
    if sysname == 'Linux':
        linux_main()
    elif sysname == 'pyboard':
        pyboard_main()
    else:
        print("Unrecognized sysname: {}".format(sysname))
        sys.exit()

main()

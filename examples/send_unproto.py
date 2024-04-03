#!/usr/bin/env python3
# =============================================================================
# Copyright (c) 2023-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
KISS Example - Send an Unproto Message

A command line utility that sends a single Unproto message, using KISS via the
specified server.

The source and destination callsigns, along with a message, are provided on
the command line, and are encoded, using the 'ax25' module, into an AX.25
frame. This frame is then encoded as a KISS frame and sent to the server.

All of the command line arguments are required. The format is:

  send_unproto host_name:port_number call_from call_to message

The message must be enclosed in quotes on the command line.
"""

import argparse
import socket
import sys

import ax25
import kiss

# PID value for text content
_PID_TEXT = 0xF0


def get_arguments():
    """
    Get arguments from our command line.
    """
    parser = argparse.ArgumentParser(
        description='Send an Unproto message via KISS.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'host_port',
        help='<host>:<port> for KISS server')
    parser.add_argument(
        'call_from',
        help='callsign of sender')
    parser.add_argument(
        'call_to',
        help='callsign of destination')
    parser.add_argument(
        'message',
        help='message to be sent')
    args = parser.parse_args()

    # Parse and validate host and port for KISS server
    host_port = args.host_port.split(':')
    if (len(host_port) != 2
            or len(host_port[0]) < 1
            or len(host_port[1]) < 1
            or not host_port[1].isdigit()):
        raise ValueError(
            'Must provide <host_name>:<port_number> for KISS server')
    host_port[1] = int(host_port[1])

    return (args, host_port)


def create_ui_frame(call_from, call_to, message):
    """
    Create a UI frame from the provided arguments. The message is text, and
    so must be encoded into a byte sequence for the AX.25 frame.
    """
    return ax25.Frame(
        call_to,
        call_from,
        control=ax25.Control(ax25.FrameType.UI),
        pid=_PID_TEXT,
        data=message.encode('utf-8'))


def send_unproto(host, port, frame):
    """
    Connect to the server and send the provided content as a KISS frame. The
    KISS encoding is encapsulated within the send_data() method, so we simply
    need to pass the packed AX.25 frame to it. Note that no receive callback
    is provided to the connection, since we are not interested in incoming
    packets.
    """
    connection = kiss.Connection(None)
    error = None
    try:
        connection.connect_to_server(host, int(port))
    except socket.gaierror as e:
        if e.errno == socket.EAI_NONAME:
            error = 'Server name not found'
        else:
            error = 'Invalid server address'
    except ConnectionRefusedError:
        error = 'Connection refused by server'
    except Exception:
        error = 'Unknown error connecting to server'
    else:
        connection.send_data(frame.pack())
        connection.disconnect_from_server()

    return error


# Mainline code
if __name__ == "__main__":
    try:
        (args, host_port) = get_arguments()
    except ValueError as e:
        print(f'Invalid arguments: {e}')
        sys.exit(1)

    try:
        frame = create_ui_frame(args.call_from, args.call_to, args.message)
    except (TypeError, ValueError) as e:
        print(f'Invalid argument value: {e}')
        sys.exit(1)

    error = send_unproto(host_port[0], host_port[1], frame)
    if error:
        print(f'Error: {error}')
        sys.exit(1)

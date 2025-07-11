# =============================================================================
# Copyright (c) 2021-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
KISS TNC Protocol Client

A client implementation for the KISS TNC protocol, providing send and receive
capability via a TCP/IP connection. All commands are supported in sending to
the TNC; per the spec, only data frames are supported when receiving from the
TNC. Multi-port TNCs are supported.

Protocol reference:
  http://www.ka9q.net/papers/kiss.html
"""

__author__ = 'Martin F N Cooper'
__version__ = '1.0.0'

from enum import Enum
import errno
import socket
import threading


# Special characters
FEND  = b'\xC0'
FESC  = b'\xDB'
TFEND = b'\xDC'
TFESC = b'\xDD'

# Encoded special characters
ENC_FEND = b'\xDB\xDC'
ENC_FESC = b'\xDB\xDD'


DEF_HOST = '127.0.0.1'  # Default host
DEF_PORT = 8000         # Default port

WSAENOTSOCK = 10038  # Windows error raised when socket is closed


class KissException():
    @property
    def message(self):
        return self.args[0] if self.args else ''


class Command(Enum):
    """
    KISS command values as defined in the spec.

    These commands are valid only when sending.
    """
    DATA_FRAME   = 0x00
    """ Data frame """
    TX_DELAY     = 0x01
    """ Transmitter keyup delay """
    PERSISTENCE  = 0x02
    """ Persistence """
    SLOT_TIME    = 0x03
    """ Slot interval """
    TX_TAIL      = 0x04
    """ Transmitter hold up time """
    FULL_DUPLEX  = 0x05
    """ Set for full duplex, clear for half duplex """
    SET_HARDWARE = 0x06
    """ TNC-specific command """
    RETURN       = 0xFF
    """ Exit KISS mode """


class Connection:
    """
    A connection to a KISS TNC.

    Create an instance of this to communicate with the TNC. The callback
    function will be invoked with each complete KISS frame received from the
    TNC.

    :param callback: Callback function to invoke with each received frame. The
        function takes the form ``receive_callback(kiss_port, data)`` where
        ``kiss_port`` is the port number on which the frame was received, and
        ``data`` is a bytearray. Optional. Can be omitted if the client has no
        interest in received frames (e.g. for a one-shot beaconing application).
    :type callback: function or None
    """
    def __init__(self, callback):
        self._sock = None
        self._receiver = None
        self._client_callback = callback

    def connect_to_server(self, host=DEF_HOST, port=DEF_PORT):
        """
        Connect to the KISS TNC.

        Call this before any other methods on this class. It is an error to
        call this again once connected. However, an instance may be reused
        by connecting again after disconnection.

        :param str host: The host to which to connect.
        :param int port: The port on which to connect.
        """
        if self._sock:
            raise ValueError('Already connected')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        if self._client_callback:
            self._receiver = _ReceiveThread(self)
            self._receiver.start()

    def disconnect_from_server(self):
        """
        Disconnect from the KISS TNC. Do not call other methods on this class
        after this call, except to (re)connect to a server. Calling this
        method when not connected is a no-op.
        """
        if not self._sock:
            return
        if self._receiver:
            self._receiver.active = False
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
        except OSError:
            pass
        finally:
            self._sock = None
        if self._receiver:
            self._receiver.join()
            self._receiver = None

    def send_data(self, data, port=0):
        """
        Send the provided data in a data frame.

        :param data: Data to be sent.
        :type data: bytes or bytearray
        :param int port: KISS port number.
        """
        if data and len(data):
            self._send_frame(port, Command.DATA_FRAME, data)

    def set_tx_delay(self, tx_delay, port=0):
        """
        Set the transmitter keyup  delay, in 10 ms units.

        :param int tx_delay: Transmitter keyup delay.
        :param int port: KISS port number.
        """
        if tx_delay < 0 or tx_delay > 255:
            raise ValueError("Illegal tx_delay value: out of range")
        self._send_frame(port, Command.TX_DELAY, bytes([tx_delay]))

    def set_persistence(self, persistence, port=0):
        """
        Set the 'p' persistence value.

        :param int persistence: The 'p' value, in the range 0 - 255.
        :param int port: KISS port number.
        """
        if persistence < 0 or persistence > 255:
            raise ValueError("Illegal persistence value: out of range")
        self._send_frame(port, Command.PERSISTENCE, bytes([persistence]))

    def set_slot_time(self, slot_time, port=0):
        """
        Set the slot interval, in 10 ms units.

        :param int slot_time: Slot interval.
        :param int port: KISS port number.
        """
        if slot_time < 0 or slot_time > 255:
            raise ValueError("Illegal slot_time value: out of range")
        self._send_frame(port, Command.SLOT_TIME, bytes([slot_time]))

    def set_tx_tail(self, tx_tail, port=0):
        """
        Set the post-TX hold up time, in 10 ms units.

        :param int tx_tail: Transmit hold up time.
        :param int port: KISS port number.
        """
        if tx_tail < 0 or tx_tail > 255:
            raise ValueError("Illegal tx_tail value: out of range")
        self._send_frame(port, Command.TX_TAIL, bytes([tx_tail]))

    def set_full_duplex(self, full_duplex, port=0):
        """
        Set full duplex on or off.

        :param bool full_duplex: True for full duplex; False for half duplex.
        :param int port: KISS port number.
        """
        if not isinstance(full_duplex, bool):
            raise ValueError("Illegal full_duplex value: must be bool")
        self._send_frame(port, Command.FULL_DUPLEX,
                         bytes([1 if full_duplex else 0]))

    def set_hardware(self, hardware, port=0):
        """
        Set a TNC-specific hardware value.

        :param hardware: TNC-specific data.
        :type hardware: bytes or bytearray
        :param int port: KISS port number.
        """
        self._send_frame(port, Command.SET_HARDWARE, hardware)

    def send_return(self):
        """
        Send the special return command to exit KISS.
        """
        self._send_frame(0, Command.RETURN, None)

    def _send_frame(self, port, command, data):
        frame = bytearray()
        frame.extend(FEND)
        frame.append(command.value | port << 4)
        if data:
            frame.extend(_encode_special(data))
        frame.extend(FEND)
        self._sock.send(frame)

    def _frame_received(self, data):
        first_byte = data[0]
        port = first_byte & 0xF0 >> 4
        command = first_byte & 0x0F
        if command != 0:
            raise KissException("Illegal frame type received")
        self._client_callback(port, _decode_special(data[1:]))

    def _receive_data(self):
        buffer = bytearray()

        while True:
            try:
                data = self._sock.recv(_BUF_LEN)
            except OSError as e:
                if e.errno in (errno.EBADF, WSAENOTSOCK):
                    # Socket closed
                    return
                raise
            if not data:
                return
            buffer += data
            blen = len(buffer)

            while True:
                fend = buffer.find(FEND)
                if fend < 0:
                    break
                if fend > 0:
                    self._frame_received(buffer[:fend])
                buffer = buffer[fend + 1:]
                blen -= (fend + 1)


class _ReceiveThread(threading.Thread):
    def __init__(self, connection):
        self.connection = connection
        self.active = True
        super().__init__()

    def run(self):
        while self.active:
            self.connection._receive_data()


_BUF_LEN = 4096  # Buffer length for socket i/o


def _encode_special(data):
    # replace() always creates a new bytearray, so check first
    if data.find(FESC) >= 0:
        data = data.replace(FESC, ENC_FESC)
    if data.find(FEND) >= 0:
        data = data.replace(FEND, ENC_FEND)
    return data


def _decode_special(data):
    # replace() always creates a new bytearray, so check first
    if data.find(ENC_FEND) >= 0:
        data = data.replace(ENC_FEND, FEND)
    if data.find(ENC_FESC) >= 0:
        data = data.replace(ENC_FESC, FESC)
    return data

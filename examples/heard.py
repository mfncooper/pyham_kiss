#!/usr/bin/env python3
# =============================================================================
# Copyright (c) 2022-2024 Martin F N Cooper
#
# Author: Martin F N Cooper
# License: MIT License
# =============================================================================

"""
KISS Example - Heard Stations

A very simple GUI application along the lines of the Linux mheard utility,
but providing a "live" view of the most recently heard stations. A KISS
connection to, for example, Direwolf is used to retrieve packets as they
arrive. For each frame, some basic statistics are added to a displayed
list, the list being shown with the latest entry first.

Since the focus of this application is on demonstrating the simplicity of
the KISS interface, there are numerous missing features that might be
expected in a "real" application of this kind. The following are some of
the limitations. Additional features will not be added here; this example
could, however, form the basis of a more comprehensive application.

 * No storage or persistence.
 * No limit on the length of the list.
 * No ability to change sort order.
 * No display of last-frame-only values (call_to, type, mode).
 * Minimal error handling.
"""

import datetime
import platform
import queue
import socket
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

import ax25
import kiss

_DEF_HOST = '127.0.0.1'  # Default host
_DEF_PORT = 8001         # Default port


class Application(tk.Tk):
    """
    Main application, creating the UI, connecting to the KISS server and
    processing incoming data, and cleaning up on exit.
    """
    _ALARM_PERIOD = 100  # milliseconds to wait between alarms

    def __init__(self, host, port):
        super().__init__()

        # Application window title
        self.title("Heard Stations")

        # Capture the close button
        self.protocol("WM_DELETE_WINDOW", self._quit)

        # Capture Command-Q on Mac
        if platform.system() == 'Darwin':
            self.createcommand('exit', self._quit)

        # Create the UI
        self._heard_list = HeardList(self)
        self._heard_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._connection = None
        self._alarm = None
        self._frame_queue = queue.Queue()

        # Connect to the KISS server to receive packets
        self._start_receiving(host, port)

    def _quit(self):
        self._stop_receiving()
        self.destroy()

    def _start_receiving(self, host, port):
        """
        Connect to the KISS server and start receiving packets. Incoming
        packets are unpacked into frames, and added to a queue, along with
        their timestamp. The queue is necessary because our callback is
        invoked from a different thread, and we need to ensure that the
        UI code is always updated from the main thread. Adding a timestamp
        ensures that the time shown in the UI is as accurate as possible,
        given that there may be a minimal delay in processing the queue.
        """
        def receive_callback(kiss_port, data):
            frame = ax25.Frame.unpack(data)
            self._frame_queue.put((frame, datetime.datetime.now()))
        self._connection = kiss.Connection(receive_callback)
        error = None
        try:
            self._connection.connect_to_server(host, int(port))
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
            self._alarm = self.after(self._ALARM_PERIOD, self._process_frames)
        if error:
            print(error)
            self.destroy()

    def _stop_receiving(self):
        """
        Shut down the connection with the KISS server, and cancel any
        outstanding frame handling alarm.
        """
        if self._connection:
            self._connection.disconnect_from_server()
            self._connection = None
        if self._alarm:
            self.after_cancel(self._alarm)
            self._alarm = None

    def _process_frames(self):
        """
        Process any frames pending in the frame queue. For each frame,
        retrieve the required field values, and send them to the UI.
        Set an alarm so that we are called repeatedly.
        """
        while not self._frame_queue.empty():
            (frame, timestamp) = self._frame_queue.get()
            self._heard_list.add_heard(
                str(frame.src), frame.control.frame_type, timestamp)
        self._alarm = self.after(self._ALARM_PERIOD, self._process_frames)


class HeardList(ttk.Frame):
    """
    The list of heard stations. A ttk tree is used as a flat list.
    """
    _PADX = 5  # Padding on left and right of cell values
    _ROWS = 20  # Initial number of visible rows

    def __init__(self, parent):
        super().__init__(parent)

        # Add horizontal padding to entries in the list
        s = ttk.Style()
        s.configure("HeardList.Treeview.Cell", padding=(self._PADX, 0))

        # Create the list
        cols = ('call_from', 'count', 'sframes', 'uframes',
                'iframes', 'first_heard', 'last_heard')
        tree = ttk.Treeview(self, columns=cols, show='headings',
                            height=self._ROWS, style="HeardList.Treeview")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar
        sb = tk.Scrollbar(self)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        sb.config(command=tree.yview)
        tree.config(yscrollcommand=sb.set)

        # Set up columns
        tree.heading('call_from', text='Callsign')
        tree.column('call_from', width=self._char_width(9),
                    stretch=False, anchor=tk.W)
        tree.heading('count', text='Total')
        tree.column('count', width=self._char_width(6),
                    stretch=False, anchor=tk.E)
        tree.heading('sframes', text='S Frames')
        tree.column('sframes', width=self._char_width(6),
                    stretch=False, anchor=tk.E)
        tree.heading('uframes', text='U Frames')
        tree.column('uframes', width=self._char_width(6),
                    stretch=False, anchor=tk.E)
        tree.heading('iframes', text='I Frames')
        tree.column('iframes', width=self._char_width(6),
                    stretch=False, anchor=tk.E)
        tree.heading('first_heard', text='First Heard')
        tree.column('first_heard', width=self._char_width(19),
                    stretch=False, anchor=tk.W)
        tree.heading('last_heard', text='Last Heard')
        tree.column('last_heard', width=self._char_width(19),
                    stretch=False, anchor=tk.W)

        self.tree = tree

    @staticmethod
    def _char_width(count):
        """
        Calculate the width of a string of characters. This makes it easy
        to set up the correct column widths.
        """
        return tkfont.Font().measure('8' * (count + 1)) + 2 * HeardList._PADX

    def add_heard(self, callsign, frame_type, timestamp):
        """
        Add new heard information to the list. If we already have a row for
        this callsign, update the counts and timestamp, and move the row to
        the top. If we don't, add a new row at the top of the list.
        """
        frame_time = '{:%Y-%m-%d %H:%M:%S}'.format(timestamp)
        row_id = None

        # See if we already have a row for this callsign
        for child_id in self.tree.get_children():
            values = list(self.tree.item(child_id, 'values'))
            if values[0] == callsign:
                row_id = child_id
                break
        else:
            # No existing item, so create a new one
            values = [callsign, 0, 0, 0, 0, frame_time, frame_time]

        # Update counts based on the frame type
        values[1] = int(values[1]) + 1
        if frame_type.is_S():
            values[2] = int(values[2]) + 1
        elif frame_type.is_U():
            values[3] = int(values[3]) + 1
        elif frame_type.is_I():
            values[4] = int(values[4]) + 1

        # Set time last heard
        values[6] = frame_time

        if row_id:
            # Update existing item and move to top
            self.tree.item(row_id, values=values)
            self.tree.move(row_id, '', 0)
        else:
            # Add new item
            self.tree.insert('', 0, values=values)


def main():
    argc = len(sys.argv)
    if argc == 1:
        host = _DEF_HOST
        port = _DEF_PORT
    elif argc == 2:
        host = sys.argv[1]
        port = _DEF_PORT
    elif argc == 3:
        host = sys.argv[1]
        try:
            port = int(sys.argv[2])
        except ValueError:
            print('Port must be a number')
            sys.exit(1)
    else:
        print('Usage: heard [<host> [<port>]]')
        sys.exit(1)
    app = Application(host, port)
    app.mainloop()


if __name__ == "__main__":
    main()

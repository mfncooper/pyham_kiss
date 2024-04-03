.. _examples:

Examples
========

Included with this package are some complete example applications that
illustrate how the library can be used to build real world software.

.. important::
   These examples use the PyHam AX.25 package to manipulate AX.25 frames, so
   be sure to install that before running them.

   ::

   $ pip install pyham_ax25


Heard
-----

A very simple GUI application along the lines of the Linux ``mheard`` utility,
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

**Note:** If you are running on Linux and receive a Python error about the
``tkinter`` module not being found, you may need to install the python3-tk
(Ubuntu) or python3-tkinter (Fedora) package on your system.

Send Unproto
------------

A minimal command line utility that sends a single Unproto message, using KISS
via the specified server.

The source and destination callsigns, along with a message, are provided on
the command line, with the message enclosed in quotes. These values are then
encoded, using the ``ax25`` package, into an AX.25 frame, which is then in turn
encoded as a KISS frame and sent to the server.

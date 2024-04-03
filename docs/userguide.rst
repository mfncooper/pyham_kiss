.. _user_guide:

User Guide
==========

Rather than just lay out the API class by class and method by method, this
User Guide walks through some use cases for the PyHam KISS package.

For complete details of the classes and methods, see the
:doc:`API Reference <autoapi/index>`.

Receiving and decoding packets
------------------------------

Our first task will be to monitor all incoming packets so that we can watch
all of the incoming data. There are several ways in which we could do this.
We could build a command line tool that prints out each incoming packet, and
blocks until the next packet arrives. More interesting, though, is to build
a GUI application that remains responsive to the user while waiting for new
packets to arrive.

Each GUI framework provides a slightly different means of enabling some kind
of background operation so that, for example in our situation, incoming packets
can be processed as the user continues with other tasks. While we *could* build
things differently for each framework, the ``pyham_kiss`` package uses threads,
enabling a common approach to be taken.

To many, threads are a scary topic. However, there are only a couple of aspects
that are important to understand in our scenario.

- The ``pyham_kiss`` package uses a background thread to receive incoming
  packets. As each new packet arrives, it calls a function provided by the
  client and passes the decoded packet.
- Almost all GUI frameworks require that any changes made to the UI must be
  done from the main application thread. This means that we cannot simply
  update the UI from the callback function mentioned above. Instead, we must
  synchronize our updates.

Let's look at some code. The first thing we need to do is set up the code that
will start, and later stop, the background thread for receiving packets.

.. note::
   For a couple of reasons, we are going to set up our application as its own
   class. This is not strictly necessary, but it avoids the need for the use
   of the ``global`` keyword when referencing shared data. It also meshes well
   with the manner in which GUI applications are typically constructed, though
   we will avoid reference to any particular GUI framework in this guide.

Here's the bare-bones outline of our application class.

.. code-block:: python

   class Application:

       def __init__(self, host, port):
           super().__init__()

           # Connection to the KISS server
           self._connection = None

           # Synchronized queue of incoming frames
           self._frame_queue = queue.Queue()

           # Connect to the KISS server to receive packets
           self._start_receiving(host, port)

       def _quit(self):
           self._stop_receiving()

       def _start_receiving(self, host, port):
           pass

       def _stop_receiving(self):
           pass

There are a couple of things to note here.

- The ``Queue`` instance will be our means of communication between the thread
  that will be receiving incoming packets and the thread that runs the user
  interface.
- The ``_start_receiving()`` method is called right away, initiating reception
  of packets as soon as the application starts. In a more user-friendly
  application, it may be more practical to wait until the user provides the
  host and port via a form or dialog. Similarly, the ``_stop_receiving()``
  method is called on application exit, rather than upon a specific user
  request.
- Other code specific to the GUI framework's setup and teardown will be needed
  in any real application. It is skipped here for clarity and focus.

Now let's add the code to connect to the KISS server and start receiving
packets.

.. code-block:: python

       def _start_receiving(self, host, port):
           # Create a new connection instance, providing our callback
           self._connection = kiss.Connection(receive_callback)

           error = None
           try:
               # Make the connection to the KISS server
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
               # Set up a UI mechanism to handle new incoming data
               set_idle_callback(self._process_frames)
           if error:
               print(error)
               self._quit()

A few more things to note here:

- When we create the connection instance, we provide the callback that will be
  called for each incoming packet. We will see this function shortly.
- Once we have successfully connected to the server, we set up the mechanism
  that will be used to check our queue periodically for new information to be
  added to our user interface. This mechanism is specific to each GUI framework.
  Here we have called a fictional function named ``set_idle_callback()``, and
  provided it with a member function that we will see later.
- While we don't usually include this much error handling code in this guide,
  here it is illustrative of the kinds of things that could go wrong while
  attempting to connect to the server.

At this point, the ``connect_to_server()`` function has created and started a
background thread to receive incoming packets from the KISS server. Now we
need to provide the means for handling those packets. There are two parts to
this, provided, as you may have surmised, by ``receive_callback()`` and
``_process_frames()``. These functions add items to, and remove items from, our
synchronized queue, respectively.

The ``receive_callback()`` is so simple, and has so little to do, that we will
embed it within our ``_start_receiving()`` method. The callback receives the
id of the KISS port on which the packet arrived, and, of course, the packet
itself. The packet has already been decoded, so we now have the raw packet
data.

Note that the ``receive_callback()`` function is invoked within the background
thread that is receiving packets from the server. Thus it cannot interact with
the user interface directly, which is why it is putting items on to the queue
instead.

.. code-block:: python

       def _start_receiving(self, host, port):

           def receive_callback(kiss_port, data):
               frame = ax25.Frame.unpack(data)
               self._frame_queue.put((frame, datetime.datetime.now()))

In our application scenario, we are handling AX.25 packets coming from a server
such as Direwolf, so we can go ahead and unpack the frame data, using the
``pyham_ax25`` package. Once unpacked, we can add it to our queue, along with
the timestamp of its arrival, so that it can be later processed for possible
display in the user interface. In your application, you could also choose to
perform no processing at this stage and simply add the incoming raw packet to
the queue.

Recall that, using our fictional ``set_idle_callback()`` function, we told the
GUI framework that it should invoke our ``_process_frames()`` method when it
has some idle time (i.e. the application is not busy doing other things, such
as interacting with the user). Thus the ``_process_frames()`` method will be
invoked within the same thread as the user interface (typically the
application's main thread), and can update that user interface as necessary.

.. code-block:: python

       def _process_frames(self):
           while not self._frame_queue.empty():
               (frame, timestamp) = self._frame_queue.get()
               self._display_new_frame_info(frame.src, frame.dst, timestamp)

It is important to note here that,in this scenario, we are emptying the queue
of all available frames each time ``_process_frames()`` is invoked. Since we
are simply displaying the source, destination, and timestamp of each frame,
this places no noticeable load on the application, so it does not cause any
problems. However, if your application needs to do significant work with each
incoming frame, you will need to take additional measures in order to avoid
locking up the user interface, potentially processing only one or a few frames
each time ``_process_frames()`` is invoked.


Sending an Unproto message
--------------------------

A common use for KISS in conjunction with a server such as Direwolf is to send
periodic Unproto messages, perhaps as a beacon. While we won't go into the
mechanics of setting up a periodic task here, we'll see just how easy it is to
construct and send our messages.

For simplicity, we'll hardcode the details of the message we're going to send.
The first thing we need to do is create an AX.25 frame containing these details
- who it's being sent from, who it's being sent to, and the
message itself. We do this using the ``pyham_ax25`` package.

.. code-block:: python

   CALL_FROM = 'KD6YAM-2'
   CALL_TO = 'BEACON'
   MESSAGE = 'Testing, testing, 1, 2, 3'

   PID_TEXT = 0xF0  # We'll be sending plain text

   frame = ax25.Frame(
       CALL_TO,
       CALL_FROM,
       control=ax25.Control(ax25.FrameType.UI),  # Create a UI, or unproto, frame
       pid=_PID_TEXT,
       data=MESSAGE.encode('utf-8'))

Next we need to connect to the KISS server. This is *almost* the same as what
we saw for receiving packets, above.

.. code-block:: python

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
   if error:
       print(error)
       sys.exit(1)

Notice that, this time, we passed ``None`` to the ``Connection`` constructor.
This is because we're not interested here in receiving any packets; we're only
going to send a message and then exit our application. In this situation, we
don't need to create a receive callback as we did before.

All that's left is to pack up the frame we created, send it via the connection,
and then close that connection.

.. code-block:: python

   connection.send_data(frame.pack())
   connection.disconnect_from_server()

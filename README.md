# PyHam KISS

## Overview

This package provides a client implementation for the KISS TNC protocol,
providing send and receive capability via a TCP/IP connection. All commands
are supported in sending to the TNC; per the spec, only data frames are
supported when receiving from the TNC. Multi-port TNCs are supported.

This implementation has been tested with Direwolf as the server.

It is expected that developers working with this package will have some level
of knowledge of the KISS protocol. Those less familiar with the protocol may
wish to refer to the
[KISS protocol specification](http://www.ka9q.net/papers/kiss.html)
in conjunction with the documentation for this package.

**Author**: Martin F N Cooper, KD6YAM  
**License**: MIT License

### Limitations

- This package supports only TCP/IP connection to a KISS server. It does not
  support serial connection, nor are there plans to add such support.

## Installation

**Important**: This package requires Python 3.7 or later.

The PyHam KISS package is distributed on
[PyPI](https://pypi.org/project/pyham_kiss/),
and should be installed with pip as follows:

```console
$ pip install pyham_kiss
```

Then import the module in your code using:

```python
   import kiss
```

The source code is available from the
[GitHub repository](https://github.com/mfncooper/pyham_kiss):

```console
$ git clone https://github.com/mfncooper/pyham_kiss
```

## Documentation

Full documentation is available
[online](https://pyham-kiss.readthedocs.io/en/latest/)
and includes the following:

<dl>
<dt><b>User Guide</b></dt>
<dd>The User Guide walks through some use cases for the package, starting
from the basics and adding capability as it progresses.</dd>
<dt><b>Examples</b></dt>
<dd>Complete example applications are included, in order that a developer
can observe the usage of the package in a real-world scenario.</dd>
<dt><b>API Reference</b></dt>
<dd>If you are looking for information on a specific function, class, or
method, this part of the documentation is for you.</dd>
</dl>

## Discussion

If you have questions about how to use this package, the documentation should
be your first point of reference. If the User Guide, API Reference, or Examples
don't answer your questions, or you'd simply like to share your experiences
or generally discuss this package, please join the community on the
[PyHam KISS Discussions](https://github.com/mfncooper/pyham_kiss/discussions)
forum.

Note that the GitHub Issues tracker should be used only for reporting bugs or
filing feature requests, and should not be used for questions or general
discussion.

## References

<dl>
<dt>KISS protocol reference:</dt>
<dd><a href="http://www.ka9q.net/papers/kiss.html">http://www.ka9q.net/papers/kiss.html</a></dd>
<dt>Direwolf:</dt>
<dd><a href="https://github.com/wb2osz/direwolf">https://github.com/wb2osz/direwolf</a></dd>
</dl>

## About PyHam

PyHam is a collection of Python packages targeted at ham radio enthusiasts who
are also software developers. The name was born out of a need to find unique
names for these packages when the most obvious names were already taken.

PyHam packages aim to provide the kind of functionality that makes it much
simpler to build sophisticated ham radio applications without having to start
from scratch. In addition to the packages, PyHam aims to provide useful
real-world ham radio applications for all hams.

See the [PyHam home page](https://pyham.org) for more information, and a
list of currently available libraries and applications.

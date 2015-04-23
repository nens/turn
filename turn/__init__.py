# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Implementation of a serial number dispenser / wall display locking system
using redis.

How it works
------------
A user acquires a serial number unique to a resource from a dispenser. The
resource may be modified only if a second number, called the indicator,
corresponds to it.

There are two ways for the indicator for a resource to change:

1. The corresponding user is done with the modification and increases
   the number, notifying any other subscribed users. This is the preferred
   way of handling things.

2. Another user gets impatient and calls the bump procedure. This
   procedure checks if the user corresponding to the indicator is still
   active and if necessary sets the indicator to an appropriate value.

Tools
-----
The state of users and queues can be monitered by inspection of redis
values and subscription to redis channels.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse

from . import tools
from .core import Server

Server  # pyflakes


def command(command, resources, *args, **kwargs):
    return getattr(tools, command)(resources, *args, **kwargs)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__,
    )

    # server
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=6379, type=int)
    parser.add_argument('--db', default=0, type=int)

    # tools
    parser.add_argument(
        'command',
        choices=('test', 'follow', 'reset', 'status'),

    )
    parser.add_argument(
        'resources',
        nargs='*',
        metavar='RESOURCE',
        help='Resources texts.',
    )

    return parser


def main():
    """ Call command with args from parser. """
    return command(**vars(get_parser().parse_args()))

# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse

from . import tools


def command(command, resources, *args, **kwargs):
    return getattr(tools, command)(resources, *args, **kwargs)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=__doc__,
    )

    # connection to redis server
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

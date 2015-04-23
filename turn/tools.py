# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
This module provides a number of (commandline) tools to manipulate or
inspect the state of the turn system.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import Queue as queueing
import random
import re
import redis
import sys
import time
import threading

from .core import Keys
from .core import Subscription
from .core import Server

SEPARATOR = 60 * '-'


# common
def find_resources(client):
    """ Detect dispensers and return corresponding resources. """
    wildcard = Keys.DISPENSER.format('*')
    pattern = re.compile(Keys.DISPENSER.format('(.*)'))
    return [pattern.match(d).group(1)
            for d in client.scan_iter(wildcard)]


# tools
def follow(resources, *args, **kwargs):
    """ Follow publications involved with resources. """
    client = redis.Redis(**kwargs)
    if not resources:
        resources = find_resources(client)
    if not resources:
        return

    channels = [Keys.EXTERNAL.format(resource) for resource in resources]
    subscription = Subscription(client, *channels)

    while True:
        try:
            message = subscription.listen()
            if message['type'] == 'message':
                sys.stdout.write('{}\n'.format(message['data']))
                sys.stdout.flush()
        except KeyboardInterrupt:
            break


def reset(resources, *args, **kwargs):
    """ Remove dispensers and indicators for idle resources. """
    client = redis.Redis(**kwargs)
    if not resources:
        resources = find_resources(client)

    for resource in resources:
        # do not reset when there is a queue
        keys = Keys(resource)
        indicator, dispenser = map(int, client.mget(keys.indicator,
                                                    keys.dispenser))
        if dispenser - indicator + 1:
            print('{} is busy.'.format(resource))
            continue

        # do not reset when someone is incoming
        with client.pipeline() as pipe:
            try:
                pipe.watch(keys.dispenser)
                pipe.multi()
                pipe.delete(keys.dispenser, keys.indicator)
                pipe.execute()
            except redis.WatchError:
                print('{} got busy'.format(resource))


def status(resources, *args, **kwargs):
    """
    Print status report for zero or more resources.
    """
    template = '{:<50}{:>10}'
    client = redis.Redis(**kwargs)

    # resource details
    for loop, resource in enumerate(resources):
        # blank between resources
        if loop:
            print()

        # strings needed
        keys = Keys(resource)
        wildcard = keys.key('*')

        # header
        template = '{:<50}{:>10}'
        indicator = client.get(keys.indicator)
        print(template.format(resource, indicator))
        print(SEPARATOR)

        # body
        numbers = sorted([keys.number(key)
                          for key in client.scan_iter(wildcard)])
        for number in numbers:
            label = client.get(keys.key(number))
            print(template.format(label, number))

    if resources:
        return

    # find resources and queue sizes
    resources = find_resources(client)
    if not resources:
        return
    dispensers = (Keys.DISPENSER.format(r) for r in resources)
    indicators = (Keys.INDICATOR.format(r) for r in resources)
    combinations = zip(client.mget(dispensers), client.mget(indicators))
    sizes = (int(dispenser) - int(indicator) + 1
             for dispenser, indicator in combinations)

    # print sorted results
    print(template.format('Resource', 'Queue size'))
    print(SEPARATOR)
    for size, resource in sorted(zip(sizes, resources), reverse=True):
        print(template.format(resource, size))


def test(resources, *args, **kwargs):
    """
    Indefinitely add jobs to server.
    """
    # this only works with resources
    if not resources:
        return

    values = {}

    # target for the test threads
    def target(queue, server):
        """
        Test thread target.
        """
        while True:
            # pick tasks from queue
            try:
                resource, period = queue.get()
            except TypeError:
                break
            label = 'Dummy workload taking {:.2f} s'.format(period)
            # execute
            with server.lock(resource=resource, label=label):
                value = '{:x}'.format(random.getrandbits(128))
                values[resource] = value
                time.sleep(period)
                assert values[resource] == value

    # launch threads
    threads = []
    queue = queueing.Queue(maxsize=1)
    for resource in resources:
        thread = threading.Thread(
            target=target,
            kwargs={'queue': queue, 'server': Server(*args, **kwargs)},
        )
        thread.start()
        threads.append(thread)

    try:
        while True:
            queue.put((random.choice(resources), .1 + .1 * random.random()))
    except KeyboardInterrupt:
        pass

    for thread in threads:
        queue.put(None)

    for thread in threads:
        thread.join()
    return 0

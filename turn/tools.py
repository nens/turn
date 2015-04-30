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
from .core import Locker
from .core import Queue
from .core import Subscription

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
    # subscribe
    client = redis.Redis(**kwargs)
    resources = resources if resources else find_resources(client)
    channels = [Keys.EXTERNAL.format(resource) for resource in resources]
    if resources:
        subscription = Subscription(client, *channels)

    # listen
    while resources:
        try:
            message = subscription.listen()
            if message['type'] == 'message':
                sys.stdout.write('{}\n'.format(message['data']))
                sys.stdout.flush()
        except KeyboardInterrupt:
            break


def reset(resources, *args, **kwargs):
    """ Remove dispensers and indicators for idle resources. """
    test = kwargs.pop('test', False)
    client = redis.Redis(**kwargs)
    resources = resources if resources else find_resources(client)

    for resource in resources:
        # investigate sequences
        queue = Queue(client=client, resource=resource)
        values = client.mget(queue.keys.indicator, queue.keys.dispenser)
        try:
            indicator, dispenser = map(int, values)
        except TypeError:
            print('no such queue: "{}".'.format(resource))
            continue

        # do a bump if there appears to be a queue
        if dispenser - indicator + 1:
            queue.message('Reset tool bumps.')
            indicator = queue.bump()

        # do not reset when there is still a queue
        size = dispenser - indicator + 1
        if size:
            print('"{}" is in use by {} user(s).'.format(resource, size))
            continue

        # reset, except when someone is incoming
        with client.pipeline() as pipe:
            try:
                pipe.watch(queue.keys.dispenser)
                if test:
                    time.sleep(0.02)
                pipe.multi()
                pipe.delete(queue.keys.dispenser, queue.keys.indicator)
                pipe.execute()
            except redis.WatchError:
                print('activity detected for "{}".'.format(resource))


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

    # show a more general status report for all available queues
    resources = find_resources(client)
    if resources:
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
    Indefinitely add jobs to locker.
    """
    # this only works with resources
    if not resources:
        return 0

    values = {}

    # target for the test threads
    def target(queue, locker):
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
            kwargs = {'expire': 5,
                      'patience': 1,
                      'label': label,
                      'resource': resource}
            with locker.lock(**kwargs):
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
            kwargs={'queue': queue, 'locker': Locker(*args, **kwargs)},
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

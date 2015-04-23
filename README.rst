Turn
====

Introduction
------------
Turn is a resource-locking queue system using python and redis.

It is inspired on a the queueing system that is sometimes found in small
shops, consisting of a number dispener and a wall indicator.

Turn can be used inside python code to request a lock on a shared resource
and wait for green light to do safely handle that resource.

Turn comes with a commandline tool for resetting and direct inspection
of queues, and listening to message channels for one or more resources.

Installation
------------

Installation is straightforward::

    $ pip install turn

Of course, you should also have a redis server at hand.

Usage
-----

Basic usage goes like this::

    import turn

    # A server represents a particular redis client
    server = turn.Server()

    resource = 'my_valuable_resource'
    label = 'This shows up in messages.'

    with server.lock(resource=resource, label=label):
        pass  # do your careful work on the resource here

Inspection can be done using the console script requesting a snap-shot
status report::

    $ turn status my_valuable_resource
    my_valuable_resource                                       5
    ------------------------------------------------------------
    This shows up in status reports and messages.              5

Alternatively, one or more subscriptions to the redis pubsub channels
for a particular resource can be followed::

    $ turn follow my_valuable_resource
    my_valuable_resource: 5 drawn by "This shows up in messages."
    my_valuable_resource: 5 starts
    my_valuable_resource: 5 completed by "This shows up in messages."
    my_valuable_resource: 6 can start now

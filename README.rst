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

Implementation
--------------
When a lock is requested, a unique serial number is obtained from Redis
via INCR on a redis value, called the dispenser. The lock is acquired
only if another value, called the indicator, corresponds to the unique
serial number.

There are two ways for the indicator to change.

1. The user with the corresponding serial number is done with the
   modification and increases the number, notifying any other subscribed
   waiting users. This is the preferred way to handle things.

2. Another user gets impatient and calls the bump procedure. This
   procedure checks if the user corresponding to the indicator is
   still active and if necessary sets the indicator to an appropriate
   value.
   
Activity is monitored via a thread that keeps refreshing an expiring
value in Redis.

Tools
-----
The state of users and queues can be monitered by inspection of redis
values and subscription to redis channels.

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

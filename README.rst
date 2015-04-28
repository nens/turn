Turn
====


Introduction
------------
Turn is a shared-resource-locking queue system using python and Redis. Use
it in separate programs that acess the same shared resource to make
sure each program waits for its turn to handle the resource.

It is inspired on a the queueing system that is sometimes found in small
shops, consisting of a number dispener and a wall indicator.

Turn can be used in python code to request a lock on a shared resource
and wait for green light to do safely handle that resource.

Turn comes with a commandline tool for resetting and direct inspection
of queues, and listening to message channels for one or more resources.


Installation
------------

Install turn with pip::

    $ pip install turn

Of course, you should also have a Redis server at hand.


Implementation
--------------
When a lock is requested, a unique serial number is obtained from Redis
via INCR on a Redis value, called the dispenser. The lock is acquired
only if another value, called the indicator, corresponds to the unique
serial number.

There are two mechanisms that can change the indicator:

1. The user with the corresponding serial number is finished acting on the
   shared resource and increases the number, notifying any other subscribed
   waiting users. This is the preferred way to handle things.

2. Another user gets impatient and calls the bump procedure. This
   procedure checks if the user corresponding to the indicator is
   still active and if necessary sets the indicator to an appropriate
   value.
   
Activity is monitored via an expiring key-value pair in Redis. The turn
library automatically arranges a thread that keeps updating the expiration
time, to make sure the presence does not expire during waiting for,
or handling of the resource.

Tools
-----
The state of users and queues can be monitered by inspection of Redis
values and subscription to Redis channels.

Usage
-----

Basic usage goes like this::

    import turn

    # a locker corresponds to a reusable Redis client
    locker = turn.Locker(host='localhost', port=6379, db=0)

    resource = 'my_valuable_resource'
    label = 'This shows up in messages.'

    with locker.lock(resource=resource, label=label):
        pass  # do your careful work on the resource here

Inspection can be done using the console script requesting a snap-shot
status report::

    $ turn status my_valuable_resource
    my_valuable_resource                                       5
    ------------------------------------------------------------
    This shows up in status reports and messages.              5

Alternatively, one or more subscriptions to the Redis PubSub channels
for a particular resource can be followed::

    $ turn follow my_valuable_resource
    my_valuable_resource: 5 drawn by "This shows up in messages."
    my_valuable_resource: 5 starts
    my_valuable_resource: 5 completed by "This shows up in messages."
    my_valuable_resource: 6 can start now

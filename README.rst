Turn
====


Introduction
------------
Turn is a shared-resource-locking queue system using python and Redis. Use
it in separate programs that acess the same shared resource to make
sure each program waits for its turn to handle the resource.

It is inspired on a the queueing system that is sometimes found in small
shops, consisting of a number dispener and a wall indicator.

Turn comes with a commandline tool for resetting and direct inspection
of queues, and listening to message channels for one or more resources.


Installation
------------

Install turn with pip::

    $ pip install turn

Of course, you should also have a Redis server at hand.


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

lock() accepts two extra keyword arguments:

expire: maximum expire value for a users presence (default 60)

If a user crashes hard, its presence in the queue will be kept
alive at most ``expire`` seconds. This value affects how often the EXPIRE
command will be sent to redis to signal the continuing presence of a
user in the queue.

patience: period of waiting before bumping the queue (default 60)

If a program waits longer than this value without receiving any
progression messages on the queues pubsub channel, it will bump the
queue to see if any users have left the queue in an unusual way.


Tools
-----
The state of users and queues can be monitered by inspection of Redis
values and subscription to Redis channels.

Inspection can be done using the console script requesting a snap-shot
status report::

    $ turn status my_valuable_resource --host localhost
    my_valuable_resource                                       5
    ------------------------------------------------------------
    This shows up in status reports and messages.              5

Running ``turn status`` without specifying any resources, produces a summary
of all queues within the database.

Alternatively, one or more subscriptions to the Redis PubSub channels
for a particular resource can be followed::

    $ turn follow my_valuable_resource --port 6379
    my_valuable_resource: 5 assigned to "This shows up in messages."
    my_valuable_resource: 5 started
    my_valuable_resource: 5 completed by "This shows up in messages."
    my_valuable_resource: 6 granted

Similar to the status command, running ``turn follow`` without specifying
any resources starts following the channels for any queue currently
within the database. Note that new queues are not automatically added
to the subscription.

Queues can also be reset (removed) from redis using ``turn reset``
optionally followed by resources queues to reset. Reset without
resource names resets all available queues in the server. If a queue
for a resource shows activity, it will not be reset and in addition a
message will be produced.


Implementation details
----------------------
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

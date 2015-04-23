Turn
====

Introduction
------------
Turn is a distributed resource locking queue system using python and
redis. With it a process thread can request a lock on a shared resource
and wait for green light to do its work safely.

Turn comes with a number of tools for inspection of the queues or the
pubsub system for one or more resources.

Installation
------------
```
python bootstrap.py
bin/buildout
```

Usage
-----

Basic usage goes like this:
```python
from scripts import turn
server = turn.Server()

resource = 'my_valuable_resource'
label = 'This shows up in status reports and messages.'

with server.lock(resource=resource, label=label):
    pass  # do your careful work on the resource here
```

Inspection can be done using the console script:

```
$ turn status my_valuable_resource
my_valuable_resource                                       5
------------------------------------------------------------
This shows up in status reports and messages.              5
```

```
$ turn follow my_valuable_resource
my_valuable_resource: 5 drawn by "This shows up in status reports and messages."
my_valuable_resource: 5 starts
my_valuable_resource: 5 completed by "This shows up in status reports and messages."
my_valuable_resource: 6 can start now
```

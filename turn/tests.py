# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import signal
import sys
import threading
import time
import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from turn import console
from turn import tools
from turn import core


class TestBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resource = 'test_resource'
        cls.label = 'test_label'
        cls.locker = core.Locker()
        cls.kwargs = {'expire': 2,
                      'patience': 1,
                      'label': cls.label,
                      'resource': cls.resource}

    @classmethod
    def lock(cls, delay=0):
        time.sleep(delay)
        with cls.locker.lock(**cls.kwargs):
            pass

    @classmethod
    def tearDownClass(cls):
        cls.lock()
        tools.reset(resources=[cls.resource])


class TestCore(TestBase):

    @classmethod
    def setUpClass(cls):
        cls.resource = 'test_resource'
        cls.label = 'test_label'
        cls.locker = core.Locker()
        cls.kwargs = {
            'resource': cls.resource,
            'label': cls.label,
            'expire': 2,
            'patience': 1,
        }

    def crash(self):
        with self.locker.lock(**self.kwargs):
            raise RuntimeError()

    def lock_hastily(self):
        kwargs = self.kwargs.copy()
        kwargs['patience'] = 0
        with self.locker.lock(**kwargs):
            pass

    def test_subscription(self):
        client = self.locker.client
        channel = 'test_channel'
        subscription = core.Subscription(client, channel)
        message = subscription.listen()

        # no message
        self.assertIsNone(subscription.listen(timeout=0.01))

        # message
        message = 'test_message'
        client.publish(channel, 'test_message')
        self.assertEqual(subscription.listen()['data'], message)

    def test_keeper(self):
        client = self.locker.client
        key = 'test_key'
        label = 'test_label'
        keeper = core.Keeper(client=client, key=key, label=label, expire=60)
        time.sleep(0.01)
        self.assertEqual(client.get(key), label)
        keeper.close()
        self.assertIsNone(client.get(key))

    def test_crash(self):
        self.assertRaises(RuntimeError, self.crash)
        tools.reset(resources=[self.resource])

    def test_patience(self):
        thread1 = threading.Thread(target=self.lock)
        thread2 = threading.Thread(target=self.lock_hastily)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()


class TestTools(TestBase):

    def setUp(self):
        # one cycle to have a predictable state
        self.lock()
        tools.reset(resources=[self.resource])

        # swap stdout with fresh StringIO
        self.stdout, sys.stdout = sys.stdout, StringIO()

    def tearDown(self):
        # swap back
        self.stdout, sys.stdout = sys.stdout, self.stdout

    def kill(self, pid):
        time.sleep(0.01)
        os.kill(pid, signal.SIGINT)

    def interact(self, pid):
        self.lock(0.01)
        self.kill(pid)

    def test_follow(self):
        # run, lock, kill
        thread = threading.Thread(target=self.interact, args=[os.getpid()])
        thread.start()
        tools.follow(resources=[self.resource])
        thread.join()

        # join thread, swap back, evaluate
        self.assertEqual(sys.stdout.getvalue(), (
            'test_resource: 1 assigned to "test_label"\n'
            'test_resource: 1 started\n'
            'test_resource: 1 completed by "test_label"\n'
            'test_resource: 2 granted\n'
        ))

    def test_follow_any(self):
        self.lock()  # there must be something to follow
        thread = threading.Thread(target=self.kill, args=[os.getpid()])
        thread.start()
        tools.follow(resources=[])
        thread.join()

    def test_reset_success(self):
        self.lock()
        tools.reset(resources=[self.resource])
        self.assertEqual(sys.stdout.getvalue(), '')

    def test_reset_no_queue(self):
        tools.reset(resources=[self.resource])
        expected = 'No such queue: "test_resource".\n'
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_reset_busy(self):
        with self.locker.lock(**self.kwargs):
            tools.reset(resources=[self.resource])
        expected = '"test_resource" is in use by 1 user(s).\n'
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_reset_watch(self):
        self.lock()  # as opposed to the no queue case
        thread = threading.Thread(target=self.lock, args=[0.01])
        thread.start()
        tools.reset(resources=[self.resource], test=True)
        thread.join()
        expected = 'Activity detected for "test_resource".\n'
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_status(self):
        # need another resource to print the white line
        other_resource = 'test_resource_other'
        with self.locker.lock(resource=other_resource):
            pass

        with self.locker.lock(**self.kwargs):
            tools.status(resources=[self.resource, other_resource])

        # cleanup the other resource
        tools.reset(resources=[other_resource])

        expected = (
            'test_resource                                              1\n'
            '------------------------------------------------------------\n'
            'test_label                                                 1\n'
            '\n'
            'test_resource_other                                        2\n'
            '------------------------------------------------------------\n'
        )
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_status_any(self):
        with self.locker.lock(**self.kwargs):
            tools.status(resources=[])
        line = 'test_resource                                              1'
        self.assertIn(line, sys.stdout.getvalue().split('\n'))


class TestConsole(unittest.TestCase):

    def test_console(self):
        argv = sys.argv
        connection = ['--host', 'localhost', '--port', '6379', '--db', '0']
        sys.argv = [''] + connection + ['status']
        status = console.main()
        self.assertFalse(status)
        sys.argv = argv

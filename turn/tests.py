# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import random
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
        cls.kwargs = {'patience': 0.01,
                      'label': cls.label,
                      'resource': cls.resource}

    @classmethod
    def lock(cls):
        with cls.locker.lock(**cls.kwargs):
            pass

    @classmethod
    def tearDownClass(cls):
        cls.cycle()  # one cycle to silently leave without traces

    @classmethod
    def cycle(cls):
        # creates or activates and removes the test queue
        cls.lock()
        time.sleep(0.01)
        tools.reset(resources=[cls.resource])
        time.sleep(0.01)

    # helpers
    def kill(self):
        os.kill(os.getpid(), signal.SIGINT)

    def kill_later(self):
        time.sleep(0.01)
        self.kill()


class TestCore(TestBase):

    def lock_and_crash(self):
        with self.locker.lock(**self.kwargs):
            raise RuntimeError()

    def lock_verify(self, sleep):
        with self.locker.lock(**self.kwargs):
            value = '{:x}'.format(random.getrandbits(128))
            self.value = value
            time.sleep(0.01)
            self.assertEqual(value, self.value)

    def lock_short(self):
        self.lock_verify(0.01)

    def lock_long(self):
        self.lock_verify(0.02)

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

    def test_reset_dead_queue(self):
        self.assertRaises(RuntimeError, self.lock_and_crash)
        tools.reset(resources=[self.resource])

    def test_crash_going(self):
        thread1 = threading.Thread(target=self.lock_short)
        thread2 = threading.Thread(target=self.lock_short)
        thread1.start()
        thread2.start()
        self.assertRaises(RuntimeError, self.lock_and_crash)
        tools.reset(resources=[self.resource])
        thread1.join()
        thread2.join()
        self.cycle()

    def test_crash_waiting(self):
        thread1 = threading.Thread(target=self.lock_short)
        thread2 = threading.Thread(target=self.lock_short)
        thread3 = threading.Thread(target=self.kill_later)
        thread1.start()
        thread2.start()
        thread3.start()
        self.assertRaises(KeyboardInterrupt, self.lock_long)
        thread1.join()
        thread2.join()
        thread3.join()
        self.cycle()


class TestTools(TestBase):

    def setUp(self):
        self.cycle()  # one cycle to have a predictable state

        # swap stdout with fresh StringIO
        self.stdout, sys.stdout = sys.stdout, StringIO()

    def tearDown(self):
        # swap back
        self.stdout, sys.stdout = sys.stdout, self.stdout

    # helpers
    def lock_later(self):
        time.sleep(0.01)
        self.lock()

    def lock_and_kill_later(self):
        self.lock_later()
        self.kill_later()

    # follow
    def test_follow(self):
        thread = threading.Thread(target=self.lock_and_kill_later)
        thread.start()
        tools.follow(resources=[self.resource])
        thread.join()
        expected = (
            'test_resource: 1 assigned to "test_label"\n'
            'test_resource: 1 started\n'
            'test_resource: 1 completed by "test_label"\n'
            'test_resource: 2 granted\n'
        )
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_follow_any(self):
        self.lock()  # there must be something to follow
        thread = threading.Thread(target=self.kill_later)
        thread.start()
        tools.follow(resources=[])
        thread.join()

    # lock
    # def test_lock(self):
    #   # thread1 = threading.Thread(target=tools.lock,
    #                              # kwargs={'resources': [self.resource]})
    #   # thread2 = threading.Thread(target=self.kill_later)
    #   # thread1.start()
    #   # thread2.start()
    #   # thread1.join()
    #   # thread2.join()

    # reset
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
            time.sleep(0.01)
            tools.reset(resources=[self.resource])
        expected = '"test_resource" is in use by 1 user(s).\n'
        self.assertEqual(sys.stdout.getvalue(), expected)

    def test_reset_watch(self):
        self.lock()  # as opposed to the no queue case
        thread = threading.Thread(target=self.lock_later)
        thread.start()
        tools.reset(resources=[self.resource], test=True)
        thread.join()
        expected = 'Activity detected for "test_resource".\n'
        self.assertEqual(sys.stdout.getvalue(), expected)

    # status
    def test_status(self):
        # need another resource to print the white line
        other_resource = 'test_resource_other'
        with self.locker.lock(resource=other_resource):
            pass

        with self.locker.lock(**self.kwargs):
            time.sleep(0.01)
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

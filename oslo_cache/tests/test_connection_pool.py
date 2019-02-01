# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time

import mock
from pymemcache.client import hash as pymemcache_hash
from six.moves import queue
import testtools
from testtools import matchers

from oslo_cache import _memcache_pool
from oslo_cache import exception
from oslo_cache.tests import test_cache


class _TestConnectionPool(_memcache_pool.ConnectionPool):
    destroyed_value = 'destroyed'

    def _create_connection(self):
        return mock.MagicMock()

    def _destroy_connection(self, conn):
        conn(self.destroyed_value)


class TestConnectionPool(test_cache.BaseTestCase):
    def setUp(self):
        super(TestConnectionPool, self).setUp()
        self.unused_timeout = 10
        self.maxsize = 2
        self.connection_pool = _TestConnectionPool(
            maxsize=self.maxsize,
            unused_timeout=self.unused_timeout)
        self.addCleanup(self.cleanup_instance('connection_pool'))

    def cleanup_instance(self, *names):
        """Create a function suitable for use with self.addCleanup.

        :returns: a callable that uses a closure to delete instance attributes
        """

        def cleanup():
            for name in names:
                if hasattr(self, name):
                    delattr(self, name)
        return cleanup

    def test_get_context_manager(self):
        self.assertThat(self.connection_pool.queue, matchers.HasLength(0))
        with self.connection_pool.acquire() as conn:
            self.assertEqual(1, self.connection_pool._acquired)
        self.assertEqual(0, self.connection_pool._acquired)
        self.assertThat(self.connection_pool.queue, matchers.HasLength(1))
        self.assertEqual(conn, self.connection_pool.queue[0].connection)

    def test_cleanup_pool(self):
        self.test_get_context_manager()
        newtime = time.time() + self.unused_timeout * 2
        non_expired_connection = _memcache_pool._PoolItem(
            ttl=(newtime * 2),
            connection=mock.MagicMock())
        self.connection_pool.queue.append(non_expired_connection)
        self.assertThat(self.connection_pool.queue, matchers.HasLength(2))
        with mock.patch.object(time, 'time', return_value=newtime):
            conn = self.connection_pool.queue[0].connection
            with self.connection_pool.acquire():
                pass
            conn.assert_has_calls(
                [mock.call(self.connection_pool.destroyed_value)])
        self.assertThat(self.connection_pool.queue, matchers.HasLength(1))
        self.assertEqual(0, non_expired_connection.connection.call_count)

    def test_acquire_conn_exception_returns_acquired_count(self):
        class TestException(Exception):
            pass

        with mock.patch.object(_TestConnectionPool, '_create_connection',
                               side_effect=TestException):
            with testtools.ExpectedException(TestException):
                with self.connection_pool.acquire():
                    pass
            self.assertThat(self.connection_pool.queue,
                            matchers.HasLength(0))
            self.assertEqual(0, self.connection_pool._acquired)

    def test_connection_pool_limits_maximum_connections(self):
        # NOTE(morganfainberg): To ensure we don't lockup tests until the
        # job limit, explicitly call .get_nowait() and .put_nowait() in this
        # case.
        conn1 = self.connection_pool.get_nowait()
        conn2 = self.connection_pool.get_nowait()

        # Use a nowait version to raise an Empty exception indicating we would
        # not get another connection until one is placed back into the queue.
        self.assertRaises(queue.Empty, self.connection_pool.get_nowait)

        # Place the connections back into the pool.
        self.connection_pool.put_nowait(conn1)
        self.connection_pool.put_nowait(conn2)

        # Make sure we can get a connection out of the pool again.
        self.connection_pool.get_nowait()

    def test_connection_pool_maximum_connection_get_timeout(self):
        connection_pool = _TestConnectionPool(
            maxsize=1,
            unused_timeout=self.unused_timeout,
            conn_get_timeout=0)

        def _acquire_connection():
            with connection_pool.acquire():
                pass

        # Make sure we've consumed the only available connection from the pool
        conn = connection_pool.get_nowait()

        self.assertRaises(exception.QueueEmpty, _acquire_connection)

        # Put the connection back and ensure we can acquire the connection
        # after it is available.
        connection_pool.put_nowait(conn)
        _acquire_connection()


class TestMemcacheClientPool(test_cache.BaseTestCase):

    def test_memcache_client_pool_create_connection(self):
        urls = [
            "foo",
            "http://foo",
            "http://bar:11211",
            "http://bar:8080",
            "https://[2620:52:0:13b8:5054:ff:fe3e:1]:8080",
            # testing port format is already in use in ipv6 format
            "https://[2620:52:0:13b8:8080:ff:fe3e:1]:8080",
            "https://[2620:52:0:13b8:5054:ff:fe3e:1]",
            "https://[::192.9.5.5]",
        ]
        mcp = _memcache_pool.MemcacheClientPool(urls=urls,
                                                arguments={},
                                                maxsize=10,
                                                unused_timeout=10)
        mc = mcp._create_connection()
        self.assertTrue(type(mc) is pymemcache_hash.HashClient)
        self.assertTrue("foo:11211" in mc.clients)
        self.assertTrue("http://foo:11211" in mc.clients)
        self.assertTrue("http://bar:11211" in mc.clients)
        self.assertTrue("http://bar:8080" in mc.clients)
        self.assertTrue("https://[2620:52:0:13b8:5054:ff:fe3e:1]:8080" in
                        mc.clients)
        self.assertTrue("https://[2620:52:0:13b8:8080:ff:fe3e:1]:8080" in
                        mc.clients)
        self.assertTrue("https://[2620:52:0:13b8:5054:ff:fe3e:1]:11211" in
                        mc.clients)
        self.assertTrue("https://[::192.9.5.5]:11211" in mc.clients)

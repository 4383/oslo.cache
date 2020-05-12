from oslo_config import fixture as config_fixture

from oslo_cache import core as cache
from oslo_cache.tests.poc import test_base


class TestMemcachePoolCacheBackend(test_base.BaseTestCaseCacheBackend):
    def setUp(self):
        self.config_fixture = self.useFixture(config_fixture.Config())
        self.config_fixture.config(
            group='cache',
            backend='oslo_cache.memcache_pool',
            enabled=True,
            proxies=['oslo_cache.testing.CacheIsolatingProxy'],
            memcache_servers=['127.0.0.1:11211']
        )
        # NOTE(hberaud): super must be called after all to ensure that
        # config fixture is properly settled.
        super(TestMemcachePoolCacheBackend, self).setUp()

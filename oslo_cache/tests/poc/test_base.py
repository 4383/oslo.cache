from oslo_utils import uuidutils

from oslotest import base

from oslo_cache import core as cache


NO_VALUE = cache.NO_VALUE


class BaseTestCaseCacheBackend(base.BaseTestCase):

    def setUp(self):
        super(BaseTestCaseCacheBackend, self).setUp()
        if not getattr(self, 'config_fixture'):
            raise Exception("Functional tests base class can't be used "
                            "directly first you should define a test class "
                            "backend wrapper to init the related "
                            "config fixture")
        self.region = cache.create_region()
        cache.configure_cache_region(self.config_fixture.conf, self.region)
        self.region_kwargs = cache.create_region(
            function=cache.kwarg_function_key_generator
        )
        cache.configure_cache_region(
            self.config_fixture.conf,
            self.region_kwargs
        )

    def test_backend_get_missing_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key))

    def test_backend_set_none_as_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        self.region.set(random_key, None)
        self.assertIsNone(self.region.get(random_key))

    def test_backend_set_blank_as_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        self.region.set(random_key, "")
        self.assertEqual("", self.region.get(random_key))

    def test_backend_set_same_key_multiple_times(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        self.region.set(random_key, "dummyValue")
        self.assertEqual("dummyValue", self.region.get(random_key))

        dict_value = {'key1': 'value1'}
        self.region.set(random_key, dict_value)
        self.assertEqual(dict_value, self.region.get(random_key))

        self.region.set(random_key, "dummyValue2")
        self.assertEqual("dummyValue2", self.region.get(random_key))

    def test_backend_multi_set_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        random_key1 = uuidutils.generate_uuid(dashed=False)
        random_key2 = uuidutils.generate_uuid(dashed=False)
        random_key3 = uuidutils.generate_uuid(dashed=False)
        mapping = {random_key1: 'dummyValue1',
                   random_key2: 'dummyValue2',
                   random_key3: 'dummyValue3'}
        self.region.set_multi(mapping)
        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key))
        self.assertFalse(self.region.get(random_key))
        self.assertEqual("dummyValue1", self.region.get(random_key1))
        self.assertEqual("dummyValue2", self.region.get(random_key2))
        self.assertEqual("dummyValue3", self.region.get(random_key3))


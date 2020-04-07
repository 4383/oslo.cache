# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
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

import os

from oslo_config import cfg
from oslo_config import fixture as config_fixture
from oslo_utils import uuidutils

from oslotest import base

from oslo_cache import core as cache


CONF = cfg.CONF

NO_VALUE = cache.NO_VALUE


class TestCacheBackend(base.BaseTestCase):

    def setUp(self):
        super(TestCacheBackend, self).setUp()
        # NOTE(hberaud): Retrieving the needed configs from env vars
        # and initializing a config fixture to use them.
        backend = os.getenv('OS_CACHE__BACKEND')
        # NOTE(hberaud): For functional tests backend is mandatory to
        # avoid to use the default backend (in memory).
        if not backend:
            raise Exception("A backend should be specified for "
                            "functional testing")
        # NOTE(hberaud): Other configs can be none and if something
        # went wrong during execution then we suppose that the zuul job
        # is misconfigured for the given backend and you should verify first
        # which config should be passed in this the related context.
        backend_arguments = os.getenv('OS_CACHE__BACKEND_ARGUMENTS')

        self.config_fixture = self.useFixture(config_fixture.Config())
        self.config_fixture.config(
            group='cache',
            backend=backend,
            enabled=True,
            backend_argument=backend_arguments)
        cache.configure(CONF)
        self.region = cache.create_region()
        cache.configure_cache_region(CONF, self.region)

    def test_backend_get_missing_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key))

    def test_backend_set_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        self.region.set(random_key, "dummyValue")
        self.assertEqual("dummyValue", self.region.get(random_key))

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

    def test_backend_multi_get_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        random_key1 = uuidutils.generate_uuid(dashed=False)
        random_key2 = uuidutils.generate_uuid(dashed=False)
        random_key3 = uuidutils.generate_uuid(dashed=False)
        mapping = {random_key1: 'dummyValue1',
                   random_key2: '',
                   random_key3: 'dummyValue3'}
        self.region.set_multi(mapping)

        keys = [random_key, random_key1, random_key2, random_key3]
        results = self.region.get_multi(keys)
        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, results[0])
        self.assertEqual("dummyValue1", results[1])
        self.assertEqual("", results[2])
        self.assertEqual("dummyValue3", results[3])

    def test_backend_multi_set_should_update_existing(self):
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
        self.assertEqual("dummyValue1", self.region.get(random_key1))
        self.assertEqual("dummyValue2", self.region.get(random_key2))
        self.assertEqual("dummyValue3", self.region.get(random_key3))

        mapping = {random_key1: 'dummyValue4',
                   random_key2: 'dummyValue5'}
        self.region.set_multi(mapping)
        self.assertEqual(NO_VALUE, self.region.get(random_key))
        self.assertEqual("dummyValue4", self.region.get(random_key1))
        self.assertEqual("dummyValue5", self.region.get(random_key2))
        self.assertEqual("dummyValue3", self.region.get(random_key3))

    def test_backend_multi_set_get_with_blanks_none(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        random_key1 = uuidutils.generate_uuid(dashed=False)
        random_key2 = uuidutils.generate_uuid(dashed=False)
        random_key3 = uuidutils.generate_uuid(dashed=False)
        random_key4 = uuidutils.generate_uuid(dashed=False)
        mapping = {random_key1: 'dummyValue1',
                   random_key2: None,
                   random_key3: '',
                   random_key4: 'dummyValue4'}
        self.region.set_multi(mapping)
        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key))
        self.assertEqual("dummyValue1", self.region.get(random_key1))
        self.assertIsNone(self.region.get(random_key2))
        self.assertEqual("", self.region.get(random_key3))
        self.assertEqual("dummyValue4", self.region.get(random_key4))

        keys = [random_key, random_key1, random_key2, random_key3, random_key4]
        results = self.region.get_multi(keys)

        # should return NO_VALUE as key does not exist in cache
        self.assertEqual(NO_VALUE, results[0])
        self.assertEqual("dummyValue1", results[1])
        self.assertIsNone(results[2])
        self.assertEqual("", results[3])
        self.assertEqual("dummyValue4", results[4])

        mapping = {random_key1: 'dummyValue5',
                   random_key2: 'dummyValue6'}
        self.region.set_multi(mapping)
        self.assertEqual(NO_VALUE, self.region.get(random_key))
        self.assertEqual("dummyValue5", self.region.get(random_key1))
        self.assertEqual("dummyValue6", self.region.get(random_key2))
        self.assertEqual("", self.region.get(random_key3))

    def test_backend_delete_data(self):
        random_key = uuidutils.generate_uuid(dashed=False)
        self.region.set(random_key, "dummyValue")
        self.assertEqual("dummyValue", self.region.get(random_key))

        self.region.delete(random_key)
        # should return NO_VALUE as key no longer exists in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key))

    def test_backend_multi_delete_data(self):
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
        self.assertEqual("dummyValue1", self.region.get(random_key1))
        self.assertEqual("dummyValue2", self.region.get(random_key2))
        self.assertEqual("dummyValue3", self.region.get(random_key3))
        self.assertEqual(NO_VALUE, self.region.get("InvalidKey"))

        keys = mapping.keys()

        self.region.delete_multi(keys)

        self.assertEqual(NO_VALUE, self.region.get("InvalidKey"))
        # should return NO_VALUE as keys no longer exist in cache
        self.assertEqual(NO_VALUE, self.region.get(random_key1))
        self.assertEqual(NO_VALUE, self.region.get(random_key2))
        self.assertEqual(NO_VALUE, self.region.get(random_key3))

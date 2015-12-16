# -*- coding: utf-8 -*-

import __builtin__
import unittest

from art3dutils.models import populate_session, ATTR_TYPES
from art3d_hydra.filters.standard import data_filter
from art3d_hydra.iterators.standard import JSONIterator
from ConfigParser import SafeConfigParser as _SafeConfigParser

session = populate_session('sqlite:///', True)


class CommandTest(unittest.TestCase):

    def setUp(self):
        self.config = _SafeConfigParser()
        self.config.read('config.ini')

    def tearDown(self):
        pass

    def test_json_iterator(self):
        data_map = self.config.items('input_data:map')
        iterator = JSONIterator(data_map=data_map)
        path = self.config.get('input_data', 'path')
        iterator.load_objects(path=path, root_container='JSONDataResult')
        for apt_dict in iterator:
            for attr_name, alias in data_map:
                self.assertIn(attr_name, apt_dict)

    def test_data_filter(self):
        data_map = self.config.items('input_data:map')
        iterator = JSONIterator(data_map=data_map,
                                filters=[data_filter])
        path = self.config.get('input_data', 'path')
        iterator.load_objects(path=path, root_container='JSONDataResult')
        for apt_dict in iterator:
            for attr_name, value in apt_dict.items():
                if value:
                    type_to_check = getattr(__builtin__,
                                            ATTR_TYPES[attr_name][1])
                    self.assertEqual(type(value), type_to_check)
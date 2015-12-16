import os
import abc
import json
import codecs
from urllib2 import urlopen, URLError
from art3dutils.utilities import (read_cell, ALPHA, progressbar, read_attr,
                                  read_child, process_value, in_shorthand)
from art3d_hydra.utils import import_from
from art3d_hydra.filters.standard import required_filter


class BasicIterator(object):
    """Basic abstract data iterator"""
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self.objects = []
        self.filters = []
        self.config = config
        self.project_title = config.get('DEFAULT', 'project_title')

        self.data_map = None
        if self.config.has_section('iterator:data_map'):
            self.data_map = config.items('iterator:data_map')[2:]

        if self.config.has_option('input_data', 'filters'):
            filter_names = self.config.get('input_data',
                                           'filters').split(', ')
            for filter_name in filter_names:
                try:
                    filter_ = import_from(
                        'art3d_hydra.'
                        'filters.{0}'.format(self.project_title),
                        filter_name)
                except (ImportError, AttributeError):
                    filter_ = import_from('art3d_hydra.filters.standard',
                                          filter_name)
                self.filters.append(filter_)
        if config.has_option('input_data', 'source'):
            self.source_location = config.get('input_data', 'source')
            self.data_string = None
            if 'http' in self.source_location or 'ftp' in self.source_location:
                try:
                    print('Connecting to remote URL...')
                    source_file = urlopen(self.source_location)
                    self.data_string = source_file.read()
                except URLError:
                    print('URL {0} is not '
                          'reachable!'.format(self.source_location))
            # elif 'ftp' in self.source_location:

            else:
                project_input_dir = config.get('paths:input', 'project')
                self.source_location = os.path.join(project_input_dir,
                                                    self.source_location)
                try:
                    with codecs.open(self.source_location, 'r', 'utf-8') as f:
                        self.data_string = f.read()
                except UnicodeDecodeError:
                    with open(self.source_location, 'r') as f:
                        self.data_string = f.read()

        if self.config.has_option('input_data', 'preparators'):
            prep_names = self.config.get('input_data',
                                         'preparators').split(', ')
            for prep_name in prep_names:
                try:
                    preparator = import_from(
                        'art3d_hydra.'
                        'preparators.{0}'.format(self.project_title),
                        prep_name)
                except (ImportError, AttributeError):
                    preparator = import_from(
                        'art3d_hydra.preparators.standard',
                        prep_name)
                self.data_string = preparator(self.data_string)

        self.load_objects()

    @abc.abstractmethod
    def load_objects(self):
        """Load objects from source to `self.objects`"""
        return

    def __iter__(self):
        """Iterator predicate"""
        return self

    def __len__(self):
        """Iterator predicate"""
        #TODO make sure calling popped list is ok
        return len(self.objects)

    def _dict_preprocessor(self, lot_dict):
        """Prepare apartment dict with optional processor callable"""

        if not required_filter(lot_dict):
            return None

        #set defaults
        if self.config.has_section('iterator:defaults'):
            for attr_name, value in self.config.items('iterator:defaults')[2:]:
                if attr_name not in lot_dict \
                        or lot_dict[attr_name] in ['0', u'0', ' ', u' ', '-']:
                    lot_dict[attr_name] = value

        #process value maps
        for attr_name, alias_value in lot_dict.items():
            section_name = 'iterator:{attr}_map'.format(attr=attr_name)
            if self.config.has_section(section_name):
                default_value = None
                if self.config.has_option(section_name, 'default'):
                    default_value = self.config.has_option(section_name,
                                                           'default')
                if not alias_value:
                    lot_dict[attr_name] = default_value
                else:
                    lot_dict[attr_name] = \
                        self.config.get(section_name,
                                        alias_value.encode('utf-8'))

        #process filters
        for filter_ in self.filters:
            lot_dict = filter_(lot_dict)

        #process exclusions
        if self.config.has_option('iterator', 'exclude'):
            victim_shorthand = self.config.get('iterator', 'exclude')
            if in_shorthand(lot_dict, victim_shorthand):
                return None

        return lot_dict

    def next(self):
        """Iterator predicate"""
        if not self.objects:
            raise StopIteration
        else:
            apartment_dict = self.objects.pop()
            return self._dict_preprocessor(apartment_dict)


class ExcelIterator(BasicIterator):

    def load_objects(self):

        import xlrd
        wb = xlrd.open_workbook(file_contents=self.data_string)
        start_row = self.config.getint('iterator', 'start_row')

        sheets = []
        if self.config.has_option('iterator', 'sheets'):
            sheet_names = self.config.get('iterator', 'sheets').split(', ')
            for sheet_name in sheet_names:
                sheet = wb.sheet_by_name(sheet_name=sheet_name.decode('utf-8'))
                sheets.append(sheet)
        else:
            sheets = wb.sheets()

        for sheet in sheets:
            row_range = range(start_row, sheet.nrows)
            if row_range:
                print(u'Processing sheet `{0}`...'.format(sheet.name)).encode('utf-8')
                for row_num in progressbar(row_range):
                    apt_dict = dict()
                    for attr, letters in self.data_map:
                        letters = letters.split(', ')
                        if len(letters) > 1:
                            apt_dict[attr] = list()
                            for letter in letters:
                                apt_dict[attr].append(
                                    read_cell(sheet, row_num,
                                              ALPHA.index(letter),
                                              'unicode')
                                )
                        else:
                            try:
                                apt_dict[attr] = read_cell(sheet,
                                                           row_num,
                                                           ALPHA.index(letters[0]),
                                                           'unicode')
                                #xfx = sheet.cell_xf_index(row_num, ALPHA.index(letters[0]))
                                #xf = wb.xf_list[xfx]
                                #bgx = xf.background.pattern_colour_index
                                #print(letters[0], apt_dict[attr], bgx)

                            except ValueError:
                                pass
                    if self.config.has_option('iterator', 'row_number'):
                        substitute_attr = self.config.get('iterator',
                                                          'row_number')
                        apt_dict[substitute_attr] = row_num
                    if self.config.has_option('iterator', 'sheet_name'):
                        substitute_attr = self.config.get('iterator',
                                                          'sheet_name')
                        apt_dict[substitute_attr] = process_value(sheet.name)
                    self.objects.append(apt_dict)


class XMLIterator(BasicIterator):
    """A basic XML iterator"""

    def load_objects(self):
        """Load data with included `data_filter` behaviour"""
        from xml.dom.minidom import parseString

        try:
            data = parseString(self.data_string)
        except UnicodeEncodeError:
            data = parseString(self.data_string.encode('utf-8'))

        target_node = self.config.get('iterator', 'target_node')
        nodes = data.getElementsByTagName(target_node)
        childnodes_mode = False
        if self.config.has_option('iterator', 'childnodes'):
            childnodes_mode = self.config.getboolean('iterator', 'childnodes')
        print('Loading nodes...')
        for node in progressbar(nodes):
            apt_dict = dict()
            if self.data_map:
                for attr, aliases in self.data_map:
                    aliases = aliases.split(', ')
                    attr_value = dict()
                    for alias in aliases:
                        if not childnodes_mode:
                            attr_value[alias] = read_attr(node, alias, 'unicode')
                        else:
                            attr_value[alias] = read_child(node, alias, 'unicode')
                    apt_dict[attr] = attr_value
                    if len(attr_value) is 1:
                        key, value = attr_value.popitem()
                        apt_dict[attr] = value
            else:
                node_attrs = node.attributes.keys()
                for attr_name in node_attrs:
                    apt_dict[attr_name] = read_attr(node, attr_name, 'unicode')
            self.objects.append(apt_dict)


class JSONIterator(BasicIterator):
    """A basic JSON iterator"""

    def load_objects(self):
        data = json.loads(self.data_string)
        if data:
            if self.config.has_option('iterator', 'root_container'):
                root_container = self.config.get('iterator',
                                                 'root_container')
                data = data[root_container]
            print('Loading JSON objects...')
            for obj in progressbar(data):
                apt_dict = dict()
                if self.data_map:
                    for attr, alias in self.data_map:
                        try:
                            apt_dict[attr] = process_value(obj[alias],
                                                           'unicode')
                        except KeyError:
                            pass
                else:
                    for attr, value in obj.items():
                        apt_dict[attr] = value
                self.objects.append(apt_dict)

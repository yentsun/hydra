import abc
import json

from collections import OrderedDict
from mako.template import Template
from scroll.models import Tablet
from hydra.utils import import_from
import art3dutils.utilities as utils
from art3dutils.models import ApartmentError


class BasicRenderer(object):
    """Basic abstract renderer"""
    __metaclass__ = abc.ABCMeta
    asset = None
    default_format = None

    def __init__(self, entity, config):
        self.entity = entity
        self.config = config
        self.output_path = None
        self.input_path = config.get('paths:input', 'project')
        filters = []
        if config.has_option('entity:basic_renderer', 'filters'):
            filter_names = config.get('entity:basic_renderer',
                                      'filters').split(', ')
            for filter_name in filter_names:
                filter_ = import_from('art3d_hydra.'
                                      'filters.{0}'
                                      .format(config.get('entity:basic_renderer',
                                                         'project_title')),
                                      filter_name)
                filters.append(filter_)
            for filter_ in filters:
                filter_(self.entity, config)

    def render(self, format_=None):
        """Render resource"""
        format_ = format_ or self.default_format
        render_method = getattr(self, 'render_{0}'.format(format_))
        try:
            self.set_output_path(format_)
        except KeyError:
            pass
        render_method()

    def set_output_path(self, format_=None, entity=None):
        """
        Define output path for an asset being rendered
        Make directories for it
        """
        config = self.config
        entity = entity or self.entity
        entity_id = None
        if config.has_section(entity.fs_name):
            if config.has_option(entity.fs_name,
                                 '{0}_id_pattern'.format(self.asset)):
                id_pattern = self.config.get(entity.fs_name,
                                             '{0}_id_pattern'.format(self.asset))
                entity_id = id_pattern.format(**entity)
            else:
                entity_id = config.get(entity.fs_name,
                                       'id_pattern').format(**entity)
        if config.has_option('paths:output',
                             '{0}_{1}'.format(entity.fs_name,
                                              self.asset)):
            output_path = config.get(
                'paths:output',
                '{0}_{1}'.format(entity.fs_name,
                                 self.asset)).format(entity=entity.fs_name,
                                                     asset=self.asset,
                                                     id=entity_id,
                                                     format=format_,
                                                     **entity)
        else:
            output_path = config.get('paths:output',
                                     'entity_asset').format(entity=entity.fs_name,
                                                            asset=self.asset,
                                                            id=entity_id,
                                                            format=format_,
                                                            **entity)
        utils.create_dirs_in_path(output_path)
        self.output_path = output_path
        return self.output_path


class ImageRenderer(BasicRenderer):
    """Render png image for an entity"""

    asset = 'image'
    default_format = 'png'

    def render_png(self):
        width = self.config.getint(self.entity.fs_name, 'width')
        height = self.config.getint(self.entity.fs_name, 'height')
        png = Tablet(self.output_path, size=(width, height))
        svg_path = svg_data = None
        try:
            svg_path = self.entity.pick_file(
                self.config.get('paths:input',
                                'entity').format(entity=self.entity.fs_name))
        except (OSError, ApartmentError) as error:
            autocrop = self.config.getboolean('apartment:image_renderer',
                                              'autocrop')
            if self.entity.fs_name == 'apartment' and autocrop:
                walls_width = 12
                if self.config.has_option('apartment', 'walls_width'):
                    walls_width = self.config.getint('apartment', 'walls_width')
                svg_data = self.entity.clip_from_floor(
                    '{0}/floor'.format(self.input_path), walls_width)
                # with open(self.set_output_path('svg', self.entity), 'w') as f:
                #     f.write(svg_data)
            else:
                raise error
        if self.config.has_section(
                '{0}:image_renderer'.format(self.entity.fs_name)):
            dict_ = dict()
            for attr, value in self.config.items(
                    '{0}:image_renderer'.format(self.entity.fs_name))[2:]:
                dict_[attr] = value
            svg_data = utils.mass_set_attr(dict_,
                                           svg_path=svg_path,
                                           svg_data=svg_data)
            png.add_svg(svg_data=svg_data)
        if self.config.has_section(
                '{0}:image_renderer_text'.format(self.entity.fs_name)):
            dict_ = dict()
            for attr, value in self.config.items(
                    '{0}:image_renderer_text'.format(self.entity.fs_name))[2:]:
                dict_[attr] = value
            svg_data = utils.mass_set_attr(dict_,
                                           svg_path=svg_path,
                                           svg_data=svg_data,
                                           tag_names=('text',))
            png.add_svg(svg_data=svg_data)
        else:
            png.add_svg(svg_path=svg_path, svg_data=svg_data)
        png.render()


class ApartmentImageRenderer(ImageRenderer):
    """Compatibility class. ImageRenderer copy"""


class BuildingImageRenderer(ImageRenderer):
    """Compatibility class. ImageRenderer copy"""


class FloorImageRenderer(ImageRenderer):
    """Compatibility class. ImageRenderer copy"""


class SectionImageRenderer(ImageRenderer):
    """Compatibility class. ImageRenderer copy"""


class FloorDataRenderer(BasicRenderer):
    """Render floor data"""

    asset = 'data'
    default_format = 'html'

    def render_html(self):
        entity = self.entity
        filename_pattern = self.config.get(self.entity.fs_name, 'id_pattern')
        filename = filename_pattern.format(**entity)
        svg_dir = self.config.get('paths:input',
                                  'entity').format(entity=self.entity.fs_name)
        apt_id_pattern = self.config.get('apartment', 'id_pattern')
        width = self.config.getint(self.entity.fs_name, 'width')
        height = self.config.getint(self.entity.fs_name, 'height')

        template_path = 'templates/{0}_html.mako'.format(self.entity.fs_name)

        try:
            custom_template_path = '{0}/{1}_html.mako'\
                .format(self.config.get('paths:input', 'project'),
                        self.entity.fs_name)
            with open(custom_template_path):
                template_path = custom_template_path
        except IOError:
            pass
        with open(self.output_path, 'w') as f:
            sort_by = self.config.get('floor', 'sort_by')
            reverse = False
            if self.config.has_option('project', 'reverse'):
                reverse_shorthand = self.config.get('project', 'reverse')
                reverse = self.entity.apartments[0]\
                    .in_shorthand(reverse_shorthand)
            html_template = Template(filename=template_path)
            contents = html_template.render(entity=entity,
                                            filename=filename,
                                            svg_dir=svg_dir,
                                            apt_id_pattern=apt_id_pattern,
                                            width=width, height=height,
                                            sort_by=sort_by, reverse=reverse)
            f.write(contents)


class BuildingDataRenderer(FloorDataRenderer):
    """Compatibility class. FloorDataRenderer copy"""


class ProjectDataRenderer(BasicRenderer):
    """Basic data.json renderer"""

    asset = 'data'
    default_format = 'json'
    minified = False

    def render_json(self):
        project = self.entity
        import codecs
        import art3dutils.models as models

        output_file_path = self.output_path
        config = self.config
        dict_ = OrderedDict()

        #add additional fields if any
        if config.has_section('project:extras'):
            extra_attribs = dict()
            for attrib, short_type in config.items('project:extras'):
                extra_attribs[attrib] = tuple(short_type.split(', '))
            models.ATTR_TYPES.update(extra_attribs)

        filters = []
        if config.has_option('project:data_renderer', 'filters'):
            filter_names = config.get('project:data_renderer',
                                      'filters').split(', ')
            config.remove_option('project:data_renderer', 'filters')
            for filter_name in filter_names:
                filter_ = import_from('art3d_hydra.'
                                      'filters.{0}'.format(project.title),
                                      filter_name)
                filters.append(filter_)

        for entity, attribs in config.items('project:data_renderer')[2:]:
            id_pattern = config.get(entity, 'id_pattern')
            dict_['{0}s'.format(entity)] = OrderedDict()
            print('Rendering {0}s...'.format(entity))
            entity_class = import_from('art3dutils.models', entity.title())
            instances = entity_class.fetch_all(project.title)
            for instance in utils.progressbar(instances):
                instance_dict = OrderedDict()

                for attrib in attribs.split(', '):
                    short, typ = models.ATTR_TYPES[attrib]
                    value = getattr(instance, attrib)
                    instance_dict[short] = utils.process_value(value, typ)

                    # insert fixed room counts
                    if attrib == 'available_detail' \
                       and config.has_option('project', 'room_counts'):
                        room_counts = config.get('project',
                                                 'room_counts').split(', ')
                        room_counts = [int(rc) for rc in room_counts]
                        room_counts.append('t')
                        instance_dict[short] = dict()
                        for rc in room_counts:
                            if rc in instance.available_detail:
                                instance_dict[short][rc] = \
                                    instance.available_detail[rc]
                            else:
                                instance_dict[short][rc] = 0

                    # calc total cost
                    if attrib == 'total_cost' and not value:
                        instance_dict[short] = instance.calc_total_cost()

                    # check note for json
                    if attrib == 'note':
                        try:
                            instance_dict[short] = json.loads(value)
                        except (TypeError, ValueError):
                            pass
                for filter_ in filters:
                    filter_(instance_dict, instance)
                try:
                    key = id_pattern.format(**instance)
                except TypeError:
                    key = id_pattern.format(
                        building_number=instance.building_number,
                        number=instance.number)
                dict_['{0}s'.format(entity)][key] = instance_dict

        utils.create_dirs_in_path(output_file_path)
        with codecs.open(output_file_path, 'w', 'utf-8') as f:
            if not self.minified:
                data_string = json.dumps(dict_, ensure_ascii=False, indent=2,
                                         separators=(',', ':'))
            else:
                data_string = json.dumps(dict_, ensure_ascii=False)
            f.write(data_string)

    def render_xls(self):
        """Render data as Excel file"""
        project = self.entity
        from xlwt import Workbook, easyxf

        workbook = Workbook()
        heading_xf = easyxf('font: bold on; align: wrap on, '
                            'vert centre, horiz center')
        sheet = workbook.add_sheet('apartment')
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(1)
        sheet.set_remove_splits(True)
        attribs = self.config.get('project:data_renderer',
                                  'apartment').split(', ')
        for attr_num, name in enumerate(attribs):
            sheet.col(attr_num).width = 256 * (len(name) + 3)
            sheet.write(0, attr_num, name, heading_xf)
        sheet.write(0, len(attribs), 'pl', heading_xf)
        entity_class = import_from('art3dutils.models', 'Apartment')
        instances = entity_class.fetch_all(project.title)
        for num, instance in enumerate(utils.progressbar(instances)):
            for attr_num, name in enumerate(attribs):
                sheet.write(num+1, attr_num, getattr(instance, name))
            sheet.write(num+1, len(attribs), getattr(instance, 'pl'))
        workbook.save(self.output_path)


class ProjectExtradataRenderer(BasicRenderer):
    """Apartment outlines, etc data renderer"""
    asset = 'data'
    default_format = 'json'

    def render_json(self):
        config = self.config
        project = self.entity
        dict_ = OrderedDict()
        dict_['outlines'] = dict()
        from art3dutils.models import Apartment
        lots = Apartment.fetch_all(project.title)
        floor_dir = (config.get('paths:input',
                                'entity')).format(entity='floor')
        width = config.getint('floor', 'width')
        height = config.getint('floor', 'height')
        for lot in lots:
            file_name = lot.pick_file(floor_dir, False)
            id_ = '{0}-p{1}'.format(file_name, lot.pl)
            dict_['outlines'][id_] = lot.area_coords(floor_dir,
                                                           (width, height))

import os
import transaction
from ConfigParser import SafeConfigParser
from pyramid.response import Response
from pyramid.view import view_config
import art3dutils.models as models
import art3dutils.utilities as utils
from hydra.utils import import_from


def get_config(project_title=''):
    """Return project's config merged with global config"""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    config = SafeConfigParser({'project_title': project_title, 'here': here})
    config.read(os.path.join(here, 'config.ini'))
    project_config_path = config.get('paths:input', 'config')
    config.read(project_config_path)
    return config


@view_config(route_name='projects',
             renderer='art3d_hydra:templates/projects.mako')
def projects(request):
    """Display project list"""
    config = get_config()
    with transaction.manager:
        models.populate_session(config.get('paths', 'database'))
        projects = models.Project.fetch_all()
    return {'projects': projects}


@view_config(route_name='project',
             renderer='art3d_hydra:templates/project.mako')
def project(request):
    """Display project data"""
    title = request.matchdict['title']
    config = get_config(title)
    with transaction.manager:
        models.populate_session(config.get('paths', 'database'))
        project = models.Project.fetch(title)
    return {'project': project}


@view_config(route_name='xls')
def xls(request):
    """Serve xls output"""
    title = request.matchdict['title']
    config = get_config(title)
    with transaction.manager:
        models.populate_session(config.get('paths', 'database'))
        project = models.Project.fetch(title)
    from xlwt import Workbook, easyxf

    workbook = Workbook()
    heading_xf = easyxf('font: bold on; align: wrap on, '
                        'vert centre, horiz center')
    sheet = workbook.add_sheet('apartment')
    sheet.set_panes_frozen(True)
    sheet.set_horz_split_pos(1)
    sheet.set_remove_splits(True)
    attribs = config.get('project:data_renderer',
                         'apartment').split(', ')
    for attr_num, name in enumerate(attribs):
        sheet.col(attr_num).width = 256 * (len(name) + 3)
        sheet.write(0, attr_num, name, heading_xf)
    entity_class = import_from('art3dutils.models', 'Apartment')
    instances = entity_class.fetch_all(project.title)
    for num, instance in enumerate(instances):
        for attr_num, name in enumerate(attribs):
            sheet.write(num+1, attr_num, getattr(instance, name))
    response = Response(content_type='application/vnd.ms-excel')
    workbook.save(response.body_file)
    return response

# -*- coding: utf-8 -*-

import os
import json
import codecs
import logging
from itertools import izip

from fabric.api import *
from fabric.contrib.console import *
from fabric.colors import *
from ConfigParser import SafeConfigParser
import sqlalchemy.exc

import art3dutils.models as core_models
import art3dutils.utilities as core_utils

from hydra.utils import import_from

def get_global_config(project_title=''):
    """Return global config"""
    here = os.path.dirname(env.real_fabfile)
    config = SafeConfigParser({'project_title': project_title, 'here': here})
    config.read(os.path.join(here, 'config.ini'))
    return config

def get_config(project_title=''):
    """Return project's config merged with global config"""
    config = get_global_config(project_title)
    project_config_path = config.get('paths:input', 'config')
    if project_title:
        if os.path.exists(project_config_path):
            config.read(project_config_path)
        else:
            print(red('Project `{title}` has no config!'.format(
                title=project_title)))
            raise SystemExit(0)
    return config

def get_progress(iterator, prefix='', *args, **kwargs):
    if not iterator:
        print(yellow('Empty {title}.'.format(title=prefix or 'container')))
        return []
    return core_utils.progressbar(iterator, prefix, *args, **kwargs)

def get_renderer_class(project_title, entity_name, asset):
    try:
        renderer_class = import_from(
            'hydra.renderers.{0}'.format(project_title),
            '{0}{1}Renderer'.format(entity_name.title(), asset.title()))
    except (ImportError, AttributeError):
        renderer_class = import_from(
            'hydra.renderers.standard',
            '{0}{1}Renderer'.format(entity_name.title(), asset.title()))
    return renderer_class

@task(alias='new')
def create(project_title):
    """Initialize project with given title"""
    from mako.template import Template
    config = get_global_config(project_title)

    # initialize config
    config_path = config.get('paths:input', 'config')
    if os.path.exists(config_path):
        print(red('Project `{title}` already exists!'.format(
            title=project_title)))
        raise SystemExit(0)
    core_utils.create_dirs_in_path(config_path)
    with codecs.open(config_path, 'w', 'utf-8') as f:
        template = Template(filename='templates/config.ini.mako')
        contents = template.render(project_title=project_title)
        f.write(contents)

    session = core_models.populate_session(config.get('paths', 'database'),
                                          create_tables=True)
    project = core_models.Project(project_title)
    session.add(project)
    session.commit()

    print(green('Project `{title}` created!'.format(title=project_title)))


@task
def rename(project_title, new_title):
    """Rename project"""
    config = get_config(project_title)

    project_input_dir = config.get('paths:input', 'project')
    project_output_dir = config.get('paths:output', 'project')
    repo_dir = config.get('paths', 'repo')
    new_project_input_dir = project_input_dir.replace(project_title, new_title)
    new_project_output_dir = project_output_dir.replace(project_title,
                                                        new_title)

    for root, dirs, files in os.walk(repo_dir):
        for filename in files:
            name, ext = os.path.splitext(filename)
            if name == project_title:
                os.rename(os.path.join(root, filename),
                          os.path.join(root, '{0}{1}'.format(new_title, ext)))
                print(green('Renamed {0}/{1}'.format(root, filename)))

    with quiet():
        with lcd(project_input_dir):
            renamed_input = local('mv {0} {1}'.format(project_input_dir,
                                  new_project_input_dir))
            if renamed_input.succeeded:
                print(green('Renamed {0}'.format(project_input_dir)))
        with lcd(project_output_dir):
            renamed_output = local('mv {0} {1}'.format(project_output_dir,
                                   new_project_output_dir))
            if renamed_output.succeeded:
                print(green('Renamed {0}'.format(project_output_dir)))

    session = core_models.populate_session(config.get('paths', 'database'))
    project = core_models.Project.fetch(project_title)
    project.title = new_title
    session.add(project)
    session.commit()
    execute(update, new_title)


@task(alias='list')
def show():
    """List all created projects"""
    config = get_config()
    core_models.populate_session(config.get('paths', 'database'))

    try:
        projects = core_models.Project.fetch_all()
        if len(projects):
            #title - 14 sym; # apts - 10
            print(cyan('============== =========='))
            print(cyan('TITLE          LOTS      '))
            print(cyan('============== =========='))
            project_row = '{title_str} {apt_no_str}'
            for project in projects:
                print(cyan(project_row.format(
                    title_str=project.title.ljust(14),
                    apt_no_str=len(project.fetch_apartments()))))
        else:
            print(yellow('No projects available.'))
    except sqlalchemy.exc.OperationalError:
        print(yellow('No database available.'))


@task
def check(project_title):
    """Check if project is ready for production"""
    config = get_config(project_title)
    core_models.populate_session(config.get('paths', 'database'))
    project = core_models.Project.fetch(project_title)
    if config.has_section('input_data'):
        print(green(u'Project has config.'))
    else:
        print(yellow(u'Project has no config!'))
    try:
        print(green(u'Project is in database '
                    u'and has {1:d} '
                    u'lots.'.format(project_title,
                                    len(project.fetch_apartments()))))
    except AttributeError:
        print(yellow(u'Project is not in database!'.format(project_title)))
        raise SystemExit(0)

    print('Checking lot SVGs...')
    lots = core_models.Apartment.fetch_all(project_title)
    ok_count = 0
    fail_count = 0
    input_path = config.get('paths:input', 'project')
    for lot in get_progress(lots, 'lots'):
        try:
            lot.pick_file('{0}/apartment'.format(input_path))
            lot.pick_file('{0}/floor'.format(input_path))
            ok_count += 1
        except core_models.ApartmentError:
            fail_count += 1
        except OSError:
            print(red('No SVGs in project input directory!'))
            raise SystemExit(0)
    if not fail_count:
        print(green('All lots have SVGs or polygons.'))
    elif not ok_count:
        print(red('No lots have SVGs or polygons!'))
    else:
        print(yellow('{0} out of {1} '
                     'lots have no SVGs or polygons!'.format(fail_count,
                                                             len(lots))))


@task(alias='del')
def delete(project_title):
    """Delete project files and directories"""
    config = get_config(project_title)
    session = core_models.populate_session(config.get('paths', 'database'))
    project = core_models.Project.fetch(project_title)
    if project:
        import shutil
        if confirm('Are you sure?'):
            try:
                shutil.rmtree('input/{title}'.format(title=project_title))
                shutil.rmtree('output/{title}'.format(title=project_title))
            except OSError:
                pass
            session.delete(project)
            session.commit()

            repo_dir = config.get('paths', 'repo')
            for root, dirs, files in os.walk(repo_dir):
                for filename in files:
                    name, ext = os.path.splitext(filename)
                    if name == project_title:
                        os.remove(os.path.join(root, filename))
                        print(green('Deleted {0}/{1}'.format(root, filename)))

            print(green('Project `{title}` '
                        'deleted!'.format(title=project_title)))
    else:
        print(yellow('No project named `{title}`. '
                     'Available projects:'.format(title=project_title)))
        show()


@task(alias='can')
def canonize(project_title):
    """Create a canonic JSON data file"""
    config = get_config(project_title)
    iterator_lib = config.get('input_data', 'iterator').split('.')[0]
    iterator_name = config.get('input_data', 'iterator').split('.')[1]

    apt_data = list()
    iterator_class = import_from('hydra.'
                                 'iterators.{0}'.format(iterator_lib),
                                 iterator_name)
    iterator = iterator_class(config)
    if len(iterator):
        print(cyan('Creating canonic JSON with {0}...'.format(iterator_name)))
        for apt_dict in get_progress(iterator):
            if apt_dict:
                apt_data.append(apt_dict)
        canonic_path = config.get('paths:input', 'canonic_json')
        core_utils.create_dirs_in_path(canonic_path)
        with codecs.open(canonic_path,
                         'w', 'utf-8') as f:
            f.write(json.dumps(apt_data, ensure_ascii=False, indent=2,
                               separators=(',', ':')))
    else:
        print(yellow('Iterator empty!'))


@task(alias='up')
def update(project_title, clean=False):
    """Add apartments to DB, canonize first"""
    config = get_config(project_title)
    if config.has_section('input_data'):
        execute(canonize, project_title)
    db = config.get('paths', 'database')
    session = core_models.populate_session(db, create_tables=True)

    if clean:
    #remove project
        project = core_models.Project.fetch(project_title)
        if project:
            session.delete(project)
            session.commit()

    #write new data
    print(cyan('Updating project data...'))
    canonic_json = config.get('paths:input', 'canonic_json')
    try:
        with codecs.open(canonic_json, 'r', 'utf-8') as f:
            json_data = json.load(f)
            for apt_obj in get_progress(json_data):
                if 'number' not in apt_obj:
                    apt_obj['number'] = 1
                if 'note' in apt_obj and type(apt_obj['note']) in (list, dict):
                    apt_obj['note'] = json.dumps(apt_obj['note'])
                core_models.Apartment.add(project_title, **apt_obj)
        session.commit()
    except IOError:
        print(red('No `{0}` file!'.format(canonic_json)))

    if config.has_option('database', 'post_update_filters'):
        print(cyan('Applying post-update filters...'))
        filters = []
        filter_names = config.get('database',
                                  'post_update_filters').split(', ')
        for filter_name in filter_names:
            filter_ = import_from('hydra.'
                                  'filters.{0}'.format(project_title),
                                  filter_name)
            filters.append(filter_)

        apartments = core_models.Apartment.fetch_all(project_title)
        for apartment in get_progress(apartments, 'apartments'):
            for filter_ in filters:
                filter_(apartment, config)
        session.commit()


@task(alias='out')
def render(project_title, entity_name='project', shorthand=None, assets=None,
           limit=None, format_=None, available_only=False, **filters):
    """Render materials for an entity"""

    config = get_config(project_title)
    assets = assets or config.get(entity_name, 'assets')
    core_models.populate_session(config.get('paths', 'database'))
    entity_class = import_from('art3dutils.models', entity_name.title())
    instances = entity_class.fetch_all(project_title, shorthand=shorthand,
                                       limit=limit,
                                       available_only=available_only,
                                       **filters)
    for asset in assets.split(', '):
        print(cyan('Rendering `{0}`...'.format(asset)))
        logger = setup_logging(project_title, entity_name, asset)
        renderer_class = get_renderer_class(project_title, entity_name, asset)
        container = get_progress(instances)
        if len(instances) is 1:
            container = instances
        for instance in container:
            renderer = renderer_class(instance, config)
            try:
                renderer.render(format_)
            except core_models.ApartmentError as e:
                print(red(e))
                logger.error(e)


@task(alias='mout')
def multi_render(project_title, entity_name='project', shorthand=None,
                 assets=None, limit=None, workers_count=2):
    """Multiprocessing version of `render`"""

    from multiprocessing import Queue, Process

    config = get_config(project_title)
    assets = assets or config.get(entity_name, 'assets').split(', ')

    def worker(work_queue, count):

        for key in get_progress(iter(work_queue.get, 'STOP'),
                                     length=count):
            for asset in assets:
                try:
                    renderer_class = import_from(
                        'hydra.renderers.{0}'.format(project_title),
                        '{0}{1}Renderer'.format(entity_name.title(),
                                                asset.title()))
                except (ImportError, AttributeError):
                    renderer_class = import_from(
                        'hydra.renderers.standard',
                        '{0}{1}Renderer'.format(entity_name.title(),
                                                asset.title()))
                instance_to_render = entity_class.fetch(shorthand_key=key)
                renderer = renderer_class(instance_to_render, config)
                try:
                    renderer.render()
                except core_models.ApartmentError as e:
                    print(red(e))

    core_models.populate_session(config.get('paths', 'database'))
    entity_class = import_from('art3dutils.models', entity_name.title())
    instances = entity_class.fetch_all(project_title, shorthand=shorthand,
                                       limit=limit)
    total = len(instances)
    queue = Queue()

    print(cyan('Forming queue...'))
    for instance in get_progress(instances):
        queue.put(instance.shorthand)

    workers_count = int(workers_count)
    processes = []

    print(cyan('Spawning {0} processes...'.format(workers_count)))
    for w in xrange(workers_count):
        p = Process(target=worker, args=(queue, total))
        p.start()
        processes.append(p)
        queue.put('STOP')

    for p in processes:
        p.join()


@task
def update_json(project_title):
    execute(update, project_title)
    execute(render, project_title)
    execute(deploy, project_title)


@task
def deploy(project_title, entity_name='project', shorthand=None, assets=None,
           limit=None, file_format='json', available_only=False, **filters):

    current_host = env.hosts[0]
    config = get_config(project_title)

    core_models.populate_session(config.get('paths', 'database'))
    entity_class = import_from('art3dutils.models', entity_name.title())
    instances = entity_class.fetch_all(project_title, shorthand=shorthand,
                                       limit=limit,
                                       available_only=available_only,
                                       **filters)
    role = 'staging'
    if config.has_option('remote:production', 'host'):
        production_host = config.get('remote:production', 'host')
        if current_host == production_host:
            role = 'production'
    webroot = config.get('remote:{0}'.format(role), 'webroot')
    assets = assets or config.get(entity_name, 'assets')
    for asset in assets.split(', '):
        print(cyan('*** DEPLOYING {entity}{shorthand} {asset} TO `{role}` ***'.format(
            entity=entity_name, shorthand=" {}".format(shorthand) if shorthand else '',
            asset=asset, role=role)))
        remote_asset_path = config.get(
            'paths:deployment',
            '{entity}_{asset}'.format(entity=entity_name, asset=asset))
        remote_path = '{webroot}/' \
                      '{asset_path}'.format(webroot=webroot,
                                            asset_path=remote_asset_path)
        remote_dir = os.path.dirname(remote_path)
        if shorthand:
            renderer_class = get_renderer_class(project_title, entity_name, asset)
            def local_paths_gen():
                for instance in instances:
                    entity_dir = config.get('paths:input', 'entity').format(
                        entity=instance.fs_name)
                    local_path = renderer_class(instance, config).set_output_path()
                    if os.path.exists(local_path):
                        yield local_path
                    else:
                        print(yellow("No {} for {} {}").format(asset, instance.fs_name,
                                                               instance.shorthand))
            local_paths = local_paths_gen()
        elif entity_name == 'project' and\
            asset == 'data' and \
                config.has_option('paths:output', '{0}_{1}'.format(entity_name, asset)):
            local_path = (config.get('paths:output',
                                     '{0}_{1}'.format(entity_name, asset))) \
                .format(format=file_format, entity=entity_name, asset=asset, id='')
            local_paths = [local_path]
        else:
            local_path = config.get('paths:output',
                                    'entity_asset_dir').format(entity=entity_name,
                                                               asset=asset)
            local_paths = ['{0}/*'.format(local_path)]
        remote_dir_exists = True
        with cd(remote_dir):
            with quiet():
                if run('ls').failed:
                    remote_dir_exists = False
        dir_created = None
        if not remote_dir_exists:
            with quiet():
                dir_created = run('mkdir {0}'.format(remote_dir)).succeeded
        if dir_created:
            print(cyan('Directory `{0}` created...'.format(remote_dir)))
        for instance, local_path in izip(get_progress(instances, asset),
                                         local_paths):
            put(local_path, remote_path)


@task(alias='outdep')
def render_and_deploy(*args, **kwargs):
    try:
        env.hosts[0]
    except IndexError:
        print(red('Host is not specified'))
        raise SystemExit(0)
    execute(render, *args, **kwargs)
    execute(deploy, *args, **kwargs)


@task(alias='host')
def set_hosts(project_title='', role='staging'):
    """Set hosts for further tasks"""
    config = get_config(project_title)
    staging_host = config.get('remote:{0}'.format(role), 'host')
    env.hosts = [staging_host]


@task(alias='fetch')
def fetch_remote_source(project_title):
    """Get remote data source"""
    config = get_config(project_title)
    project_input_dir = config.get('paths:input', 'project')
    local_path = os.path.join(project_input_dir,
                              config.get('input_data', 'source'))
    if config.has_option('input_data', 'remote_source'):
        remote_path = config.get('input_data', 'remote_source')
        print(cyan('Fetching remote data source...'))
        get(remote_path, local_path)
    if config.has_option('input_data', 'remote_source_directory'):
        directory_path = config.get('input_data', 'remote_source_directory')
        with cd(directory_path):
            file_name = run('find . -type f -printf %p";" | ls -t | head -1')
            print(cyan('Fetching *latest* remote data source...'))
            get(file_name, local_path)


@task(alias='set')
def mass_set_property(project_title, entity_name='apartment', **attributes):
    """Set property for all lots in project"""
    config = get_config(project_title)
    session = core_models.populate_session(config.get('paths', 'database'))
    entity_class = import_from('art3dutils.models', entity_name.title())
    instances = entity_class.fetch_all(project_title)
    container = get_progress(instances)
    for instance in container:
        for attribute_name in attributes:
            setattr(instance, attribute_name, attributes[attribute_name])
    session.commit()


def setup_logging(project_title, entity, asset):
    """Setup logging for a project"""

    config = get_config(project_title)
    output_path = config.get('paths:output', 'project')
    error_log = logging.getLogger('error_Log')
    log_path = '{0}/{1}_{2}_error.log'.format(output_path, entity, asset)
    core_utils.create_dirs_in_path(log_path)
    error_log.addHandler(logging.FileHandler(log_path, mode='w'))

    return error_log

from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config = Configurator(settings=settings)
    config.include('pyramid_mako')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('project', '/project/{title}')
    config.add_route('projects', '/projects')
    config.add_route('xls', '/xls/{title}_data.xls')
    config.scan()
    return config.make_wsgi_app()
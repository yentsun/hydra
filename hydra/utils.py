def import_from(module, name):
    """
    Dynamically import stuff from modules.
    Credit:http://stackoverflow.com/a/8790077/216042
    """
    module = __import__(module, fromlist=[name])
    return getattr(module, name)
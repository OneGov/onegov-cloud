from onegov.core.utils import module_path


def asset(path):
    """ Returns the absolute path to an asset path relative to this module. """
    return module_path('onegov.shared', 'assets' + '/' + path.lstrip('/'))

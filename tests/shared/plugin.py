from .capturelog import CaptureLogPlugin


def pytest_configure(config):

    # activate log capturing
    config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')

    # ignore deprecation warnings (we wait until things are gone)
    filters = config.getini('filterwarnings')

    if not filters:
        filters.append('ignore::DeprecationWarning')
        filters.append('ignore::PendingDeprecationWarning')

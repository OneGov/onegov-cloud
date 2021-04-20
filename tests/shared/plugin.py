from .capturelog import CaptureLogPlugin


def pytest_configure(config):

    # activate log capturing
    config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')

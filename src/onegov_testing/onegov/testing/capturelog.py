# borrowed from https://bitbucket.org/memedough/pytest-capturelog/
# adjusted to our needs (namely, we don't want the log displayed
# when the test fails)

import logging
import py
import pytest


def pytest_configure(config):
    """Activate log capturing if appropriate."""

    config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')


class CaptureLogPlugin(object):
    """Attaches to the logging module and captures log messages for each test.

    """

    def __init__(self, config):
        """Creates a new plugin to capture log messges.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """

        log_format = '%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s'
        log_date_format = None

        self.formatter = logging.Formatter(log_format, log_date_format)

    def pytest_runtest_setup(self, item):
        """Start capturing log messages for this test.

        Creating a specific handler for each test ensures that we
        avoid multi threading issues.

        Attaching the handler and setting the level at the beginning
        of each test ensures that we are setup to capture log
        messages.
        """

        # Create a handler for this test.
        item.capturelog_handler = CaptureLogHandler()
        item.capturelog_handler.setFormatter(self.formatter)

        # Attach the handler to the root logger and ensure that the
        # root logger is set to log all levels.
        root_logger = logging.getLogger()
        root_logger.addHandler(item.capturelog_handler)
        root_logger.setLevel(logging.NOTSET)

    def pytest_runtest_teardown(self, item, nextitem):

        # If the test was skipped, the setup function is as well
        if not hasattr(item, 'capturelog_handler'):
            return

        # Detach the handler from the root logger to ensure no
        # further access to the handler.
        root_logger = logging.getLogger()
        root_logger.removeHandler(item.capturelog_handler)

        # Release the handler resources.
        item.capturelog_handler.close()
        del item.capturelog_handler


class CaptureLogHandler(logging.StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self):
        """Creates a new log handler."""

        logging.StreamHandler.__init__(self)
        self.stream = py.io.TextIO()
        self.records = []

    def close(self):
        """Close this log handler and its underlying stream."""

        logging.StreamHandler.close(self)
        self.stream.close()

    def emit(self, record):
        """Keep the log records in a list in addition to the log text."""

        self.records.append(record)
        logging.StreamHandler.emit(self, record)


class CaptureLogFuncArg(object):
    """Provides access and control of log capturing."""

    def __init__(self, handler):
        """Creates a new funcarg."""

        self.handler = handler

    def text(self):
        """Returns the log text."""

        return self.handler.stream.getvalue()

    def records(self):
        """Returns the list of log records."""

        return self.handler.records

    def setLevel(self, level, logger=None):
        """Sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        obj.setLevel(level)

    def atLevel(self, level, logger=None):
        """Context manager that sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        return CaptureLogLevel(obj, level)


class CaptureLogLevel(object):
    """Context manager that sets the logging level of a handler or logger."""

    def __init__(self, obj, level):
        """Creates a new log level context manager."""

        self.obj = obj
        self.level = level

    def __enter__(self):
        """Adjust the log level."""

        self.orig_level = self.obj.level
        self.obj.setLevel(self.level)

    def __exit__(self, exc_type, exc_value, traceback):
        """Restore the log level."""

        self.obj.setLevel(self.orig_level)


@pytest.fixture
def caplog(request):
    """Returns a funcarg to access and control log capturing."""

    return CaptureLogFuncArg(request._pyfuncitem.capturelog_handler)


@pytest.fixture
def capturelog(request):
    """Returns a funcarg to access and control log capturing."""

    return CaptureLogFuncArg(request._pyfuncitem.capturelog_handler)

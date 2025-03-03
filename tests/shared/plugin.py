from .capturelog import CaptureLogPlugin
from datetime import datetime
from pytz import timezone
import pytest


def pytest_configure(config):

    # activate log capturing
    config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')
    # Add the skip_night_hours marker
    config.addinivalue_line(
        'markers',
        'skip_night_hours: mark test to skip during night hours',
    )


def pytest_runtest_setup(item):
    if "skip_night_hours" in item.keywords:
        zurich_tz = timezone('Europe/Zurich')
        current_hour = datetime.now(zurich_tz).hour
        if 22 <= current_hour or current_hour < 6:
            pytest.skip('Skipping time-dependent test during night hours.')

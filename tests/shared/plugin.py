from __future__ import annotations

import pytest
from datetime import datetime
from pytz import timezone

from .capturelog import CaptureLogPlugin


def pytest_configure(config: pytest.Config) -> None:

    # activate log capturing
    config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')
    # Add the skip_night_hours marker
    config.addinivalue_line(
        'markers',
        'skip_night_hours: mark test to skip during night hours',
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    if "skip_night_hours" in item.keywords:
        zurich_tz = timezone('Europe/Zurich')
        current_hour = datetime.now(zurich_tz).hour
        if 22 <= current_hour or current_hour < 6:
            pytest.skip('Skipping time-dependent test during night hours.')

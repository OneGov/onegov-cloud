from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import time
from onegov.core.utils import append_query_param
from sedate import to_timezone
from sedate import utcnow
from sqlalchemy.orm import Mapped
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.models import Assembly


class StartTimeMixin:

    #: The local start time
    start_time: Mapped[time | None]

    def start(self) -> None:
        self.start_time = to_timezone(utcnow(), 'Europe/Zurich').time()


class TimestampedVideoMixin(StartTimeMixin):

    if TYPE_CHECKING:
        # forward declare required attributes
        assembly: Assembly | Mapped[Assembly]

    #: The manual video timestamp of this agenda item
    video_timestamp: dict_property[str | None] = content_property()

    @property
    def calculated_timestamp(self) -> str | None:
        from onegov.landsgemeinde.utils import seconds_to_timestamp

        if not self.start_time or not self.assembly.start_time:
            return None

        seconds = (
            datetime.combine(date.today(), self.start_time)
            - datetime.combine(date.today(), self.assembly.start_time)
        ).seconds
        return seconds_to_timestamp(seconds)

    @property
    def video_url(self) -> str | None:
        from onegov.landsgemeinde.utils import timestamp_to_seconds

        video_url_base = self.assembly.video_url

        if not video_url_base:
            return None

        if self.video_timestamp:
            seconds = timestamp_to_seconds(self.video_timestamp)
            if seconds:
                return append_query_param(
                    video_url_base, 'start', str(seconds)
                )

        calculated_timestamp = self.calculated_timestamp
        if calculated_timestamp:
            seconds = timestamp_to_seconds(calculated_timestamp)
            if seconds:
                return append_query_param(
                    video_url_base, 'start', str(seconds)
                )

        return video_url_base

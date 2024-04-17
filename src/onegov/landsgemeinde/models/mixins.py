from onegov.core.utils import append_query_param

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.mixins import dict_property


class TimestampedVideoMixin:

    if TYPE_CHECKING:
        # forward declare required attributes
        video_timestamp: dict_property[str | None]
        calculated_timestamp: dict_property[str | None]

    @property
    def video_url_base(self) -> str | None:
        raise NotImplementedError()

    @property
    def video_url(self) -> str | None:
        from onegov.landsgemeinde.utils import timestamp_to_seconds

        if not self.video_url_base:
            return None

        if self.video_timestamp:
            seconds = timestamp_to_seconds(self.video_timestamp)
            if seconds:
                return append_query_param(
                    self.video_url_base, 'start', str(seconds)
                )
        elif self.calculated_timestamp:
            seconds = timestamp_to_seconds(self.calculated_timestamp)
            if seconds:
                return append_query_param(
                    self.video_url_base, 'start', str(seconds)
                )

        return self.video_url_base

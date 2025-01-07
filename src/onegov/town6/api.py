from dateutil.parser import isoparse
from functools import cached_property
from onegov.event.collections import OccurrenceCollection
from onegov.api import ApiEndpoint, ApiInvalidParamException
from onegov.gis import Coordinates


from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.town6.app import TownApp
    from onegov.event.models import Occurrence
    from onegov.core.orm.mixins import ContentMixin
    from onegov.core.orm.mixins import TimestampMixin
    from typing import TypeVar

    T = TypeVar('T')


UPDATE_FILTER_PARAMS = frozenset((
    'updated_gt',
    'updated_lt',
    'updated_eq',
    'updated_ge',
    'updated_le'
))


def filter_for_updated(
    filter_operation: str,
    filter_value: str | None,
    result: 'T'
) -> 'T':
    """
    Applies filters for several 'updated' comparisons.
    Refer to UPDATE_FILTER_PARAMS for all filter keywords.

    :param filter_operation: the updated filter operation to be applied. For
        allowed filters refer to UPDATE_FILTER_PARAMS
    :param filter_value: the updated filter value to filter for
    :param result: the results to apply the filters on
    :return: filter result
    """
    assert hasattr(result, 'for_filter')

    if filter_value is None:
        return result.for_filter(**{filter_operation: None})

    try:
        # only parse including hours and minutes
        isoparse(filter_value[:16])
    except Exception as ex:
        raise ApiInvalidParamException(f'Invalid iso timestamp for parameter'
                                       f"'{filter_operation}': {ex}") from ex
    return result.for_filter(**{filter_operation: filter_value[:16]})


class ApisMixin:

    app: 'TownApp'

    @cached_property
    def event_api(self) -> 'EventApiEndpoint':
        return EventApiEndpoint(self.app)


def get_geo_location(item: 'ContentMixin') -> dict[str, Any]:
    geo = item.content.get('coordinates', Coordinates()) or Coordinates()
    return {'lon': geo.lon, 'lat': geo.lat, 'zoom': geo.zoom}


def get_modified_iso_format(item: 'TimestampMixin') -> str:
    """
    Returns the iso format of the modified or created field of item.

    :param item: db item e.g. agency, people, membership
    :return: str iso representation of item last modification
    """
    return item.last_change.isoformat()


class EventApiEndpoint(
    ApiEndpoint['Occurrence'],
    ApisMixin
):
    app: 'TownApp'
    endpoint = 'events'
    filters = {'agency', 'person'} | UPDATE_FILTER_PARAMS

    @property
    def collection(self) -> Any:
        result = OccurrenceCollection(
            self.session,
            page=self.page or 0
        )

        for key, value in self.extra_parameters.items():
            self.assert_valid_filter(key)

            # apply different filters
            if key in UPDATE_FILTER_PARAMS:
                result = filter_for_updated(filter_operation=key,
                                            filter_value=value,
                                            result=result)

        result.batch_size = self.batch_size
        return result

    def item_data(self, item: 'Occurrence') -> dict[str, Any]:
        return {
            'title': item.title,
            'modified': get_modified_iso_format(item),
        }

    def item_links(self, item: 'Occurrence') -> dict[str, Any]:
        return {
        }

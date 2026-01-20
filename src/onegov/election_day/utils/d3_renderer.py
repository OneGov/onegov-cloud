from __future__ import annotations

from base64 import b64decode
from io import BytesIO
from io import StringIO
from json import dumps, loads
from onegov.core.custom import json
from onegov.core.utils import module_path
from onegov.election_day import _
from onegov.election_day.models import Ballot
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_connections_data
from onegov.election_day.utils.election import get_lists_data
from onegov.election_day.utils.election import get_lists_panachage_data
from onegov.election_day.utils.election_compound import get_list_groups_data
from onegov.election_day.utils.parties import get_parties_panachage_data
from onegov.election_day.utils.parties import get_party_results_data
from onegov.election_day.utils.parties import get_party_results_vertical_data
from onegov.election_day.utils.vote import get_ballot_data_by_district
from onegov.election_day.utils.vote import get_ballot_data_by_entity
from requests import post
from rjsmin import jsmin  # type:ignore[import-untyped]


from typing import overload
from typing import Any
from typing import IO
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.app import ElectionDayApp
    from translationstring import TranslationString


class D3Renderer:

    """ Provides access to the d3-renderer (github.com/seantis/d3-renderer).

    """

    def __init__(self, app: ElectionDayApp):
        self.app = app
        self.renderer = app.configuration.get('d3_renderer', '').rstrip('/')
        self.supported_charts = {
            'bar': {
                'main': 'barChart',
                'scripts': ('d3.chart.bar.js',),
            },
            'grouped': {
                'main': 'groupedChart',
                'scripts': ('d3.chart.grouped.js',),
            },
            'sankey': {
                'main': 'sankeyChart',
                'scripts': ('d3.sankey.js', 'd3.chart.sankey.js'),
            },
            'entities-map': {
                'main': 'entitiesMap',
                'scripts': ('topojson.js', 'd3.map.entities.js'),
            },
            'districts-map': {
                'main': 'districtsMap',
                'scripts': ('topojson.js', 'd3.map.districts.js'),
            }
        }

        # Read and minify the javascript sources
        self.scripts: dict[str, list[str]] = {}
        for chart in self.supported_charts:
            self.scripts[chart] = []
            for script in self.supported_charts[chart]['scripts']:
                path = module_path(
                    'onegov.election_day', 'assets/js/{}'.format(script)
                )
                with open(path) as f:
                    self.scripts[chart].append(jsmin(f.read()))

    def translate(self, text: TranslationString, locale: str | None) -> str:
        """ Translates the given string. """

        if locale is not None:
            translator = self.app.translations.get(locale)
        else:
            translator = None
        translated = translator.gettext(text) if translator else None
        return text.interpolate(translated)

    # def label(self):

    @overload
    def get_chart(
        self,
        chart: str,
        fmt: Literal['pdf'],
        data: JSON_ro,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[bytes]: ...

    @overload
    def get_chart(
        self,
        chart: str,
        fmt: Literal['svg'],
        data: JSON_ro,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str]: ...

    @overload
    def get_chart(
        self,
        chart: str,
        fmt: Literal['pdf', 'svg'],
        data: JSON_ro,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str] | IO[bytes]: ...

    def get_chart(
        self,
        chart: str,
        fmt: Literal['pdf', 'svg'],
        data: JSON_ro,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str] | IO[bytes]:
        """ Returns the requested chart from the d3-render service as a
        PNG/PDF/SVG.

        """

        assert chart in self.supported_charts
        assert fmt in ('pdf', 'svg')

        params = params or {}
        params.update({
            'data': data,
            'width': width,
            'viewport_width': width  # only used for PDF and PNG
        })

        response = post(
            '{}/d3/{}'.format(self.renderer, fmt),
            json={
                'scripts': self.scripts[chart],
                'main': self.supported_charts[chart]['main'],
                'params': loads(dumps(params).replace("'", '’'))  # noqa:RUF001
            },
            timeout=60
        )

        response.raise_for_status()

        if fmt == 'svg':
            return StringIO(response.text)
        else:
            return BytesIO(b64decode(response.text))

    @overload
    def get_map(
        self,
        map: str,
        fmt: Literal['pdf'],
        data: JSON_ro,
        year: int,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[bytes]: ...

    @overload
    def get_map(
        self,
        map: str,
        fmt: Literal['svg'],
        data: JSON_ro,
        year: int,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str]: ...

    @overload
    def get_map(
        self,
        map: str,
        fmt: Literal['svg', 'pdf'],
        data: JSON_ro,
        year: int,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str] | IO[bytes]: ...

    def get_map(
        self,
        map: str,
        fmt: Literal['pdf', 'svg'],
        data: JSON_ro,
        year: int,
        width: int = 1000,
        params: dict[str, Any] | None = None
    ) -> IO[str] | IO[bytes]:
        """ Returns the request chart from the d3-render service as a
        PNG/PDF/SVG.

        """
        mapdata = None
        path = module_path(
            'onegov.election_day',
            f'static/mapdata/{year}/{self.app.principal.id}.json'
        )
        with open(path) as f:
            mapdata = json.loads(f.read())

        params = params or {}
        params.update({
            'mapdata': mapdata,
            'canton': self.app.principal.id
        })

        return self.get_chart(f'{map}-map', fmt, data, width, params)

    @overload
    def get_list_groups_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_list_groups_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_list_groups_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_list_groups_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_list_groups_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, ElectionCompound):
            data = get_list_groups_data(item)
            if data and data.get('results'):
                chart = self.get_chart('bar', fmt, data)
        return (chart, data) if return_data else chart

    @overload
    def get_lists_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_lists_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_lists_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_lists_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_lists_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, Election):
            data = get_lists_data(item)
            if data and data.get('results'):
                chart = self.get_chart('bar', fmt, data)
        return (chart, data) if return_data else chart

    @overload
    def get_candidates_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_candidates_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_candidates_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_candidates_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_candidates_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:
        chart = None
        data = None
        if isinstance(item, Election):
            data = get_candidates_data(item)
            if data and data.get('results'):
                chart = self.get_chart('bar', fmt, data)
        return (chart, data) if return_data else chart

    @overload
    def get_connections_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_connections_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_connections_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_connections_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_connections_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, Election):
            data = get_connections_data(item)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart(
                    'sankey', fmt, data, params={'inverse': True}
                )
        return (chart, data) if return_data else chart

    @overload
    def get_seat_allocation_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_seat_allocation_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_seat_allocation_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_seat_allocation_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_seat_allocation_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, (Election, ElectionCompound)):
            data = get_party_results_vertical_data(item)
            if data and data.get('results'):
                chart = self.get_chart(
                    'grouped', fmt, data, params={'showBack': False}
                )
        return (chart, data) if return_data else chart

    @overload
    def get_party_strengths_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_party_strengths_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_party_strengths_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_party_strengths_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_party_strengths_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(
            item, (Election, ElectionCompound, ElectionCompoundPart)
        ):
            data = get_party_results_data(
                item, item.horizontal_party_strengths
            )
            if data and data.get('results'):
                if item.horizontal_party_strengths:
                    chart = self.get_chart('bar', fmt, data)
                else:
                    chart = self.get_chart(
                        'grouped', fmt, data, params={'showBack': False}
                    )
        return (chart, data) if return_data else chart

    @overload
    def get_lists_panachage_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_lists_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_lists_panachage_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_lists_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_lists_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, Election):
            data = get_lists_panachage_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart('sankey', fmt, data)
        return (chart, data) if return_data else chart

    @overload
    def get_parties_panachage_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_parties_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_parties_panachage_chart(
        self,
        item: object,
        fmt: Literal['pdf'],
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_parties_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg'],
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_parties_panachage_chart(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data = None
        if isinstance(item, (Election, ElectionCompound)):
            data = get_parties_panachage_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart('sankey', fmt, data)
        return (chart, data) if return_data else chart

    @overload
    def get_entities_map(
        self,
        item: object,
        fmt: Literal['pdf'],
        locale: str,
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_entities_map(
        self,
        item: object,
        fmt: Literal['svg'],
        locale: str,
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_entities_map(
        self,
        item: object,
        fmt: Literal['pdf'],
        locale: str,
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_entities_map(
        self,
        item: object,
        fmt: Literal['svg'],
        locale: str,
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_entities_map(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        locale: str,
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data: JSONObject_ro | None = None
        if isinstance(item, Ballot):
            data = get_ballot_data_by_entity(item)  # type:ignore[assignment]
            if data:
                label_left = _('Nay')
                label_right = _('Yay')
                tie_breaker = (
                    item.type == 'tie-breaker'
                    or item.vote.tie_breaker_vocabulary
                )
                if tie_breaker:
                    label_left = (
                        _('Direct Counter Proposal') if item.vote.direct
                        else _('Indirect Counter Proposal')
                    )
                    label_right = _('Proposal')
                params = {
                    'labelLeftHand': self.translate(label_left, locale),
                    'labelRightHand': self.translate(label_right, locale),
                }
                year = item.vote.date.year
                chart = self.get_map(
                    'entities', fmt, data, year, params=params
                )
        return (chart, data) if return_data else chart

    @overload
    def get_districts_map(
        self,
        item: object,
        fmt: Literal['pdf'],
        locale: str,
        return_data: Literal[False] = False,
    ) -> IO[bytes] | None: ...

    @overload
    def get_districts_map(
        self,
        item: object,
        fmt: Literal['svg'],
        locale: str,
        return_data: Literal[False] = False,
    ) -> IO[str] | None: ...

    @overload
    def get_districts_map(
        self,
        item: object,
        fmt: Literal['pdf'],
        locale: str,
        return_data: Literal[True],
    ) -> tuple[IO[bytes] | None, Any | None]: ...

    @overload
    def get_districts_map(
        self,
        item: object,
        fmt: Literal['svg'],
        locale: str,
        return_data: Literal[True],
    ) -> tuple[IO[str] | None, Any | None]: ...

    def get_districts_map(
        self,
        item: object,
        fmt: Literal['svg', 'pdf'],
        locale: str,
        return_data: bool = False,
    ) -> IO[Any] | tuple[IO[Any] | None, Any | None] | None:

        chart = None
        data: JSONObject_ro | None = None
        if isinstance(item, Ballot):
            data = get_ballot_data_by_district(item)  # type:ignore[assignment]
            if data:
                label_left = _('Nay')
                label_right = _('Yay')
                tie_breaker = (
                    item.type == 'tie-breaker'
                    or item.vote.tie_breaker_vocabulary
                )
                if tie_breaker:
                    label_left = (
                        _('Direct Counter Proposal') if item.vote.direct
                        else _('Indirect Counter Proposal')
                    )
                    label_right = _('Proposal')
                params = {
                    'labelLeftHand': self.translate(label_left, locale),
                    'labelRightHand': self.translate(label_right, locale),
                }
                year = item.vote.date.year
                chart = self.get_map(
                    'districts', fmt, data, year, params=params
                )
        return (chart, data) if return_data else chart

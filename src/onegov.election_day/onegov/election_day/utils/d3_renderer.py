from base64 import b64decode
from io import BytesIO
from io import StringIO
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.core.custom import json
from onegov.election_day import _
from onegov.election_day.views.election.candidates \
    import view_election_candidates_data
from onegov.election_day.views.election.connections \
    import view_election_connections_data
from onegov.election_day.views.election.lists import view_election_lists_data
from onegov.election_day.views.election.lists_panachage import \
    view_election_lists_panachage_data
from onegov.election_day.views.election.party_strengths \
    import view_election_party_strengths_data
from onegov.election_day.views.election_compound.party_strengths \
    import view_election_compound_party_strengths_data
from onegov.core.utils import module_path
from requests import post
from rjsmin import jsmin


class D3Renderer():

    """ Provides access to the d3-renderer (github.com/seantis/d3-renderer).

    """

    def __init__(self, app):
        self.app = app
        self.renderer = app.configuration.get('d3_renderer').rstrip('/')
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
            'map': {
                'main': 'ballotMap',
                'scripts': ('topojson.js', 'd3.chart.map.js'),
            }
        }

        # Read and minify the javascript sources
        self.scripts = {}
        for chart in self.supported_charts:
            self.scripts[chart] = []
            for script in self.supported_charts[chart]['scripts']:
                path = module_path(
                    'onegov.election_day', 'assets/js/{}'.format(script)
                )
                with open(path, 'r') as f:
                    self.scripts[chart].append(jsmin(f.read()))

    def translate(self, text, locale):
        """ Translates the given string. """

        translator = self.app.translations.get(locale)
        return text.interpolate(translator.gettext(text))

    def get_chart(self, chart, fmt, data, width=1000, params=None):
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

        response = post('{}/d3/{}'.format(self.renderer, fmt), json={
            'scripts': self.scripts[chart],
            'main': self.supported_charts[chart]['main'],
            'params': params
        })

        response.raise_for_status()

        if fmt == 'svg':
            return StringIO(response.text)
        else:
            return BytesIO(b64decode(response.text))

    def get_map(self, fmt, data, year, width=1000, params=None):
        """ Returns the request chart from the d3-render service as a
        PNG/PDF/SVG.

        """
        mapdata = None
        path = module_path(
            'onegov.election_day',
            'static/mapdata/{}/{}.json'.format(
                year,
                self.app.principal.id
            )
        )
        with open(path, 'r') as f:
            mapdata = json.loads(f.read())

        params = params or {}
        params.update({
            'mapdata': mapdata,
            'canton': self.app.principal.id
        })

        return self.get_chart('map', fmt, data, width, params)

    def get_lists_chart(self, item, fmt, return_data=False):
        chart = None
        data = None
        if isinstance(item, Election):
            data = view_election_lists_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('bar', fmt, data)
        return (chart, data) if return_data else chart

    def get_candidates_chart(self, item, fmt, return_data=False):
        chart = None
        data = None
        if isinstance(item, Election):
            data = view_election_candidates_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('bar', fmt, data)
        return (chart, data) if return_data else chart

    def get_connections_chart(self, item, fmt, return_data=False):
        chart = None
        data = None
        if isinstance(item, Election):
            data = view_election_connections_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                chart = self.get_chart(
                    'sankey', fmt, data, params={'inverse': True}
                )
        return (chart, data) if return_data else chart

    def get_party_strengths_chart(self, item, fmt, return_data=False):
        chart = None
        data = None
        if isinstance(item, Election):
            data = view_election_party_strengths_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('grouped', fmt, data)
        elif isinstance(item, ElectionCompound):
            data = view_election_compound_party_strengths_data(item, None)
            if data and data.get('results'):
                chart = self.get_chart('grouped', fmt, data)
        return (chart, data) if return_data else chart

    def get_panachage_chart(self, item, fmt, return_data=False):
        chart = None
        data = None
        if isinstance(item, Election):
            data = view_election_lists_panachage_data(item, None)
            if data and data.get('links') and data.get('nodes'):
                return self.get_chart('sankey', fmt, data)
        return (chart, data) if return_data else chart

    def get_map_chart(self, item, fmt, locale=None, return_data=False):
        chart = None
        data = None
        if isinstance(item, Ballot):
            data = item.percentage_by_entity()
            params = {
                'yay': self.translate(_('Yay'), locale),
                'nay': self.translate(_('Nay'), locale),
            }
            year = item.vote.date.year
            chart = self.get_map(fmt, data, year, params=params)
        return (chart, data) if return_data else chart

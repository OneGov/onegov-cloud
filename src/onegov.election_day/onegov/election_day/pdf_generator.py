from babel.dates import format_date
from base64 import b64decode
from copy import deepcopy
from datetime import date
from io import BytesIO
from json import loads
from onegov.ballot import Election, Vote
from onegov.core.utils import groupbylist
from onegov.core.utils import module_path
from onegov.election_day import _
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils.pdf import Pdf
from onegov.election_day.views.election import get_candidates_results
from onegov.election_day.views.election import get_connection_results
from onegov.election_day.views.election.candidates import (
    view_election_candidates_data
)
from onegov.election_day.views.election.connections import (
    view_election_connections_data
)
from onegov.election_day.views.election.lists import view_election_lists_data
from onegov.election_day.views.election.panachage import (
    view_election_panachage_data
)
from onegov.election_day.views.election.parties import (
    view_election_parties_data,
    get_party_results,
    get_party_deltas
)
from pdfdocument.document import MarkupParagraph
from requests import post
from rjsmin import jsmin
from textwrap import shorten, wrap


class PdfGenerator():

    def __init__(self, app):
        self.app = app
        self.pdf_dir = self.app.configuration.get('pdf_directory', 'pdf')
        self.renderer = app.configuration.get('d3-renderer').rstrip('/')
        self.session = self.app.session()

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
                'scripts': ('underscore.js', 'topojson.js', 'd3.chart.map.js'),
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

    def get_chart(self, chart, data, width=1000, params=None):
        """ Returns the requested chart from the d3-render service as a
        PNG/PDF/SVG.

        """

        assert chart in self.supported_charts

        params = params or {}
        params.update({
            'data': data,
            'width': width,
            'viewport_width': width  # only used for PDF and PNG
        })

        response = post('{}/d3/pdf'.format(self.renderer), json={
            'scripts': self.scripts[chart],
            'main': self.supported_charts[chart]['main'],
            'params': params
        })

        response.raise_for_status()

        return BytesIO(b64decode(response.text))

    def get_map(self, data, year, width=1000, params=None):
        """ Returns the request chart from the d3-render service as a
        PNG/PDF/SVG.

        """
        mapdata = None
        path = module_path(
            'onegov.election_day',
            'static/mapdata/{}/{}.json'.format(year, self.app.principal.id)
        )
        with open(path, 'r') as f:
            mapdata = loads(f.read())

        params = params or {}
        params.update({
            'mapdata': mapdata,
            'canton': self.app.principal.canton
        })

        return self.get_chart('map', data, width, params)

    def generate_pdf(self, item, path, locale):
        """ Generates the PDF for an election or a vote.

        Possible improvements:
        - Right align numbers / columns
        - Bottom margin for subconnection title in the table
        """

        with self.app.filestorage.open(path, 'wb') as f:

            translator = self.app.translations.get(locale)

            def translate(content):
                return content.interpolate(translator.gettext(content))

            def draw_footer(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                canvas.drawString(
                    doc.leftMargin,
                    doc.bottomMargin / 2,
                    '© {} {}'.format(
                        date.today().year,
                        self.app.principal.name
                    )
                )
                canvas.drawRightString(
                    doc.pagesize[0] - doc.rightMargin,
                    doc.bottomMargin / 2,
                    '{}'.format(canvas._pageNumber)
                )
                canvas.restoreState()

            def draw_header_and_footer(canvas, doc):
                draw_footer(canvas, doc)

                canvas.saveState()
                title = item.title_translations.get(locale) or item.title
                lines = wrap(title, 110)[:2]
                if len(lines) > 1:
                    lines[1] = shorten(lines[1], 100)
                text = canvas.beginText()
                text.setFont('Helvetica', 9)
                text.setTextOrigin(
                    doc.leftMargin,
                    doc.pagesize[1] - doc.topMargin * 2 / 3
                )
                text.textLines(lines)
                canvas.drawText(text)
                canvas.restoreState()

            pdf = Pdf(f)
            pdf.init_a4_portrait(
                page_fn=draw_footer,
                page_fn_later=draw_header_and_footer
            )

            def table_style_results(columns):
                return pdf.style.tableHead + (
                    ('ALIGN', (0, 0), (-1, columns - 1), 'LEFT'),
                    ('ALIGN', (columns, 0), (-1, -1), 'RIGHT'),
                )

            def indent_style(level):
                style = deepcopy(pdf.style.normal)
                style.leftIndent = level * style.fontSize
                return style

            # Add Header
            pdf.h1(item.title_translations.get(locale) or item.title)
            pdf.p(format_date(item.date, format='long', locale=locale))
            pdf.spacer()

            # Election
            if isinstance(item, Election):
                majorz = item.type == 'majorz'

                # Factoids
                pdf.table(
                    [
                        [
                            translate(_('Turnout')),
                            translate(_('Elegible Voters')),
                            translate(_('Received Ballots')),
                        ], [
                            '{0:.2f}%'.format(item.turnout),
                            item.elegible_voters,
                            item.received_ballots,
                        ]
                    ],
                    'even'
                )
                pdf.spacer()
                pdf.table(
                    [
                        [
                            translate(_('Mandates')),
                            translate(_('Absolute majority')) if majorz
                            else '',
                            '',
                        ], [
                            translate(_(
                                '${counted} of ${total}',
                                mapping={
                                    'counted': item.allocated_mandates,
                                    'total': item.number_of_mandates}
                            )),
                            item.absolute_majority if majorz else ''
                            ''
                        ],
                    ],
                    'even'
                )
                pdf.spacer()

                # Lists
                data = view_election_lists_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Lists')))
                    pdf.pdf(self.get_chart('bar', data))
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(_('List')),
                            translate(_('Mandates')),
                            translate(_('single_votes')),
                        ]] + [[
                            r['text'],
                            r['value2'],
                            r['value'],
                        ] for r in data['results']],
                        [4, 1, 1],
                        ratios=True,
                        style=table_style_results(1)
                    )
                    pdf.pagebreak()

                # Candidates
                data = view_election_candidates_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Candidates')))
                    pdf.pdf(self.get_chart('bar', data))
                    pdf.spacer()
                    if majorz:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('Elected')),
                                translate(_('single_votes')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                translate(_('Yes')) if r[2] else '',
                                r[3],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [4, 1, 1],
                            ratios=True,
                            style=table_style_results(2)
                        )
                    else:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('List')),
                                translate(_('Elected')),
                                translate(_('single_votes')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                r[4],
                                translate(_('Yes')) if r[2] else '',
                                r[3],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [2, 2, 1, 1],
                            ratios=True,
                            style=table_style_results(3)
                        )
                    pdf.pagebreak()

                # Connections
                data = view_election_connections_data(item, None)
                if data and data.get('links') and data.get('nodes'):
                    pdf.h2(translate(_('List connections')))
                    pdf.pdf(self.get_chart('sankey', data,
                                           params={'inverse': True}))
                    pdf.figcaption(translate(_('figcaption_connections')))
                    pdf.spacer()

                    connections = get_connection_results(item, self.session)
                    spacers = []
                    table = [[
                        '{} / {} / {}'.format(
                            translate(_('List connection')),
                            translate(_('Sublist connection')),
                            translate(_('Party'))
                        ),
                        translate(_('single_votes'))
                    ]]
                    for connection in connections:
                        table += [[
                            MarkupParagraph('{} {}'.format(
                                translate(_('List connection')),
                                connection[0]
                            ), indent_style(0)),
                            connection[1]
                        ]]
                        for sc in connection[3]:
                            table += [[
                                MarkupParagraph('{} {}'.format(
                                    translate(_('Sublist connection')),
                                    sc[0]
                                ), indent_style(1)),
                                sc[1]
                            ]]
                            table += [[
                                MarkupParagraph(l[0], indent_style(2)),
                                l[1]
                            ] for l in sc[2]]
                        table += [[
                            MarkupParagraph(l[0], indent_style(1)),
                            l[1]
                        ] for l in connection[2]]
                        spacers.append(len(table))

                    pdf.table(
                        table,
                        [5, 1],
                        ratios=True,
                        style=table_style_results(1) + tuple([
                            ('TOPPADDING', (0, row), (-1, row), 15)
                            for row in spacers[:-1]
                        ])
                    )
                    pdf.pagebreak()

                # Parties
                data = view_election_parties_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Parties')))
                    pdf.pdf(self.get_chart('grouped', data))
                    pdf.figcaption(translate(_('figcaption_parties')))
                    pdf.spacer()
                    years, parties = get_party_results(item)
                    deltas, results = get_party_deltas(item, years, parties)
                    if deltas:
                        pdf.table(
                            [[
                                translate(_('Party')),
                                translate(_('Mandates')),
                                translate(_('single_votes')),
                                translate(_('single_votes')),
                                'Δ {}'.format(years[0]),
                            ]] + [[
                                r[0],
                                r[-4],
                                r[-2],
                                r[-3],
                                r[-1],
                            ] for r in results],
                            [2, 1, 1, 1, 1],
                            ratios=True,
                            style=table_style_results(1)
                        )
                    else:
                        pdf.table(
                            [[
                                translate(_('Party')),
                                translate(_('Mandates')),
                                translate(_('single_votes')),
                                translate(_('single_votes')),
                            ]] + [[
                                r[0],
                                r[1],
                                r[3],
                                r[2],
                            ] for r in results],
                            [3, 1, 1, 1],
                            ratios=True,
                            style=table_style_results(1)
                        )
                    pdf.pagebreak()

                # Panachage
                data = view_election_panachage_data(item, None)
                if data and data.get('links') and data.get('nodes'):
                    pdf.h2(translate(_('Panachage')))
                    pdf.pdf(self.get_chart('sankey', data))
                    pdf.figcaption(translate(_('figcaption_panachage')))
                    pdf.spacer()
                    pdf.pagebreak()

                # Statistics
                pdf.h2(translate(_('Election statistics')))
                pdf.table(
                    [[
                        translate(_('Electoral District')),
                        translate(_('Turnout')),
                        translate(_('Elegible Voters')),
                        translate(_('Accounted Votes')),
                    ]] + [[
                        result.group,
                        '{0:.2f} %'.format(result.turnout),
                        result.elegible_voters,
                        result.accounted_votes,
                    ] for result in item.results] + [[
                        translate(_('Total')),
                        '{0:.2f} %'.format(item.turnout),
                        item.elegible_voters,
                        item.accounted_votes,
                    ]],
                    'even',
                    ratios=True,
                    style=table_style_results(1)
                )
                pdf.spacer()
                pdf.table(
                    [[
                        translate(_('Electoral District')),
                        translate(_('Received Ballots')),
                        translate(_('Accounted Ballots')),
                        translate(_('Blank Ballots')),
                        translate(_('Invalid Ballots')),

                    ]] + [[
                        result.group,
                        result.received_ballots,
                        result.accounted_ballots,
                        result.blank_ballots,
                        result.invalid_ballots,
                    ] for result in item.results] + [[
                        translate(_('Total')),
                        item.received_ballots,
                        item.accounted_ballots,
                        item.blank_ballots,
                        item.invalid_ballots,
                    ]],
                    'even',
                    ratios=True,
                    style=table_style_results(1)
                )
                pdf.pagebreak()

            if isinstance(item, Vote):
                # Answer
                answer = _('Rejected')
                if item.answer == 'accepted':
                    answer = _('Accepted')
                if item.counter_proposal:
                    proposal = item.proposal.accepted
                    counter_proposal = item.counter_proposal.accepted
                    if not proposal and not counter_proposal:
                        answer = _('Proposal and counter proposal rejected')
                    if proposal and not counter_proposal:
                        answer = _('Proposal accepted')
                    if not proposal and counter_proposal:
                        answer = _('Counter proposal accepted')
                    if proposal and counter_proposal:
                        if item.tie_breaker.accepted:
                            answer = _('Tie breaker in favor of the proposal')
                        else:
                            answer = _(
                                'Tie breaker in favor of the counter proposal'
                            )
                pdf.p(translate(answer))
                pdf.spacer()

                ballots = ((None, item.proposal),)
                if item.counter_proposal:
                    ballots = (
                        (_('Proposal'), item.proposal),
                        (_('Counter Proposal'), item.counter_proposal),
                        (_('Tie-Breaker'), item.tie_breaker),
                    )

                for title, ballot in ballots:
                    if title:
                        pdf.h2(translate(title))

                    # Factoids
                    pdf.table(
                        [
                            [
                                translate(_('turnout_vote')),
                                translate(_('elegible_voters_vote')),
                                translate(_('Cast Ballots')),
                            ], [
                                '{0:.2f}%'.format(ballot.turnout),
                                ballot.elegible_voters,
                                ballot.cast_ballots,
                            ]
                        ],
                        'even'
                    )
                    pdf.spacer()

                    # Map
                    if self.app.principal.use_maps:
                        data = ballot.percentage_by_entity()
                        params = {
                            'yay': translate(_('Yay')),
                            'nay': translate(_('Nay')),
                        }
                        year = item.date.year
                        pdf.pdf(self.get_map(data, year, params=params), 0.8)
                        pdf.spacer()

                    # Statistics
                    pdf.table(
                        [[
                            translate(_('Electoral District')),
                            translate(_('Result')),
                            translate(_('Yes %')),
                            translate(_('No %')),
                        ]] + [[
                            result.group,
                            translate(_('Accepted')) if result.accepted else
                            translate(_('Rejected')),
                            '{0:.2f}%'.format(result.yeas_percentage),
                            '{0:.2f}%'.format(result.nays_percentage),
                        ] for result in ballot.results] + [[
                            translate(_('Total')),
                            translate(_('Accepted')) if ballot.accepted else
                            translate(_('Rejected')),
                            '{0:.2f}%'.format(ballot.yeas_percentage),
                            '{0:.2f}%'.format(ballot.nays_percentage),
                        ]],
                        'even',
                        ratios=True,
                        style=table_style_results(2)
                    )
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(_('Electoral District')),
                            translate(_('Empty')),
                            translate(_('Invalid')),
                            translate(_('Yeas')),
                            translate(_('Nays')),
                        ]] + [[
                            result.group,
                            result.empty,
                            result.invalid,
                            result.yeas,
                            result.nays,
                        ] for result in ballot.results] + [[
                            translate(_('Total')),
                            ballot.empty,
                            ballot.invalid,
                            ballot.yeas,
                            ballot.nays,
                        ]],
                        'even',
                        ratios=True,
                        style=table_style_results(1)
                    )
                    pdf.pagebreak()

            # Add related link
            link = (item.meta or {}).get('related_link', '')
            if link:
                pdf.h2(translate(_('Related link')))
                pdf.p_markup('<a href="{link}">{link}</a>'.format(link=link))

            pdf.generate()

    def run(self, force, cleanup):
        """ Generates all PDFs for the given application.

        Only generates PDFs if not already generated since the last change of
        the election or vote. Allows to force the re-creation of the PDF.

        Optionally cleans up unused PDFs.

        """

        # Read existing PDFs
        if not self.app.filestorage.exists(self.pdf_dir):
            self.app.filestorage.makedir(self.pdf_dir)
        existing = self.app.filestorage.listdir(self.pdf_dir)

        # Get all elections and votes
        items = self.session.query(Election).all()
        items.extend(self.session.query(Vote).all())

        # Generate the PDFs
        for locale in self.app.locales:
            for item in items:
                filename = pdf_filename(item, locale)
                if (force or filename not in existing) and item.counted:
                    path = '{}/{}'.format(self.pdf_dir, filename)
                    if self.app.filestorage.exists(path):
                        self.app.filestorage.remove(path)
                    try:
                        self.generate_pdf(item, path, locale)
                    except Exception as ex:
                        # Don't leave probably broken PDFs laying around
                        if self.app.filestorage.exists(path):
                            self.app.filestorage.remove(path)
                        raise ex

        # Delete old PDFs
        if cleanup:
            existing = self.app.filestorage.listdir(self.pdf_dir)
            existing = dict(groupbylist(
                existing,
                key=lambda a: a.split('.')[0]
            ))

            # Delete orphaned files
            created = [
                pdf_filename(item, '').split('.')[0] for item in items
            ]
            for id in set(existing.keys()) - set(created):
                for name in existing[id]:
                    self.app.filestorage.remove(
                        '{}/{}'.format(self.pdf_dir, name)
                    )

            # Delete old files
            for files in existing.values():
                files = sorted(files, reverse=True)
                for name in files[len(self.app.locales):]:
                    self.app.filestorage.remove(
                        '{}/{}'.format(self.pdf_dir, name)
                    )

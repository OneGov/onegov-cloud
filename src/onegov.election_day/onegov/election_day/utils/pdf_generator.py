from babel.dates import format_date
from babel.dates import format_time
from copy import deepcopy
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import log
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.views.election import get_candidates_results
from onegov.election_day.views.election import get_connection_results
from onegov.election_day.views.election.candidates \
    import view_election_candidates_data
from onegov.election_day.views.election.party_strengths  \
    import get_party_results_deltas
from onegov.election_day.views.election.party_strengths  \
    import get_party_results
from onegov.pdf import LexworkSigner
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import Pdf
from os.path import basename
from pdfdocument.document import MarkupParagraph
from pytz import timezone
from reportlab.lib.units import cm


class PdfGenerator():

    def __init__(self, app, renderer=None):
        self.app = app
        self.pdf_dir = 'pdf'
        self.session = self.app.session()
        self.pdf_signing = self.app.principal.pdf_signing
        self.default_locale = self.app.settings.i18n.default_locale
        self.renderer = renderer or D3Renderer(app)

    def translate(self, text, locale):
        """ Translates the given string. """

        translator = self.app.translations.get(locale)
        return text.interpolate(translator.gettext(text))

    def remove(self, directory, files):
        """ Safely removes the given files from the directory. Allows to use
        wildcards.

        """
        if not files:
            return

        fs = self.app.filestorage
        for file in fs.filterdir(directory, files=files):
            path = '{}/{}'.format(directory, file.name)
            if fs.exists(path) and not file.is_dir:
                fs.remove(path)

    def sign_pdf(self, path):
        if self.pdf_signing:
            signer = LexworkSigner(
                self.pdf_signing['host'],
                self.pdf_signing['login'],
                self.pdf_signing['password']
            )
            with self.app.filestorage.open(path, 'rb') as file:
                filename = basename(path)
                reason = self.pdf_signing['reason']
                try:
                    data = signer.sign(file, filename, reason)
                except Exception as e:
                    log.error("Could not sign PDF: {}".format(e))
                    log.warning("PDF {} could not be signed".format(filename))
                    return

            self.app.filestorage.remove(path)
            with self.app.filestorage.open(path, 'wb') as f:
                f.write(data)

    def generate_pdf(self, item, path, locale):
        """ Generates the PDF for an election or a vote. """
        principal = self.app.principal

        with self.app.filestorage.open(path, 'wb') as f:

            def translate(content):
                return self.translate(content, locale)

            def format_name(item):
                return item.name if item.entity_id else translate(_("Expats"))

            pdf = Pdf(
                f,
                title=item.get_title(locale, self.default_locale),
                author=principal.name
            )
            pdf.init_a4_portrait(
                page_fn=page_fn_footer,
                page_fn_later=page_fn_header_and_footer
            )

            def table_style_results(columns):
                return pdf.style.tableHead + (
                    ('ALIGN', (0, 0), (columns - 1, -1), 'LEFT'),
                    ('ALIGN', (columns, 0), (-1, -1), 'RIGHT'),
                )

            table_style_factoids = pdf.style.table + (
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
            )

            table_style_dates = pdf.style.table + (
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),
            )

            def indent_style(level):
                style = deepcopy(pdf.style.normal)
                style.leftIndent = level * style.fontSize
                return style

            # Add Header
            pdf.h1(item.get_title(locale, self.default_locale))

            # Add dates
            changed = item.last_result_change
            if getattr(changed, 'tzinfo', None) is not None:
                tz = timezone('Europe/Zurich')
                changed = tz.normalize(changed.astimezone(tz))

            pdf.table(
                [[
                    format_date(item.date, format='long', locale=locale),
                    '{}: {} {}'.format(
                        translate(_('Last change')),
                        format_date(changed, format='long', locale=locale),
                        format_time(changed, format='short', locale=locale)

                    )
                ]],
                'even',
                style=table_style_dates
            )
            pdf.spacer()

            # Election
            if isinstance(item, Election) and item.tacit:
                # Candidates
                data = view_election_candidates_data(item, None)
                if data and data.get('results'):
                    pdf.h2(translate(_('Candidates')))
                    pdf.spacer()
                    if item.type == 'majorz':
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('Party')),
                                translate(_('Elected')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                r[3],
                                translate(_('Yes')) if r[2] else '',
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, None, 2 * cm],
                            style=table_style_results(3)
                        )
                    else:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('List')),
                                translate(_('Elected')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                r[5],
                                translate(_('Yes')) if r[2] else '',
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, None, 2 * cm],
                            style=table_style_results(3)
                        )
                    pdf.pagebreak()

            elif isinstance(item, Election):
                majorz = item.type == 'majorz'

                # Factoids
                pdf.table(
                    [
                        [
                            translate(_('Turnout')),
                            translate(_('eligible Voters')),
                            translate(_('Received Ballots')),
                        ], [
                            '{0:.2f}%'.format(item.turnout),
                            item.eligible_voters,
                            item.received_ballots,
                        ]
                    ],
                    'even',
                    style=table_style_factoids
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
                            item.absolute_majority if majorz else '',
                            ''
                        ],
                    ],
                    'even',
                    style=table_style_factoids
                )
                pdf.spacer()
                pdf.spacer()

                # Lists
                chart, data = self.renderer.get_lists_chart(item, 'pdf', True)
                if data and data.get('results'):
                    pdf.h2(translate(_('Lists')))
                    pdf.pdf(chart)
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
                        [None, 2 * cm, 2 * cm],
                        style=table_style_results(1)
                    )
                    pdf.pagebreak()

                # Candidates
                chart = self.renderer.get_candidates_chart(item, 'pdf')
                if chart:
                    pdf.h2(translate(_('Candidates')))
                    pdf.pdf(chart)
                    pdf.spacer()
                    if majorz:
                        pdf.table(
                            [[
                                translate(_('Candidate')),
                                translate(_('Party')),
                                translate(_('Elected')),
                                translate(_('single_votes')),
                            ]] + [[
                                '{} {}'.format(r[0], r[1]),
                                r[3],
                                translate(_('Yes')) if r[2] else '',
                                r[4],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, 2 * cm, 2 * cm],
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
                                r[5],
                                translate(_('Yes')) if r[2] else '',
                                r[4],
                            ] for r in get_candidates_results(
                                item, self.session
                            )],
                            [None, None, 2.3 * cm, 2 * cm],
                            style=table_style_results(3)
                        )
                    pdf.pagebreak()

                # Connections
                chart = self.renderer.get_connections_chart(item, 'pdf')
                if chart:
                    pdf.h2(translate(_('List connections')))
                    pdf.pdf(chart)
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
                        [None, 2 * cm, 2 * cm],
                        style=table_style_results(1) + tuple([
                            ('TOPPADDING', (0, row), (-1, row), 15)
                            for row in spacers[:-1]
                        ])
                    )
                    pdf.pagebreak()

                # Parties
                chart = self.renderer.get_party_strengths_chart(
                    item, 'pdf'
                )
                if chart:
                    pdf.h2(translate(_('Party strengths')))
                    pdf.pdf(chart)
                    pdf.figcaption(translate(_('figcaption_party_strengths')))
                    pdf.spacer()
                    years, parties = get_party_results(item)
                    deltas, results = get_party_results_deltas(
                        item, years, parties
                    )
                    results = results[sorted(results.keys())[-1]]
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
                                r[1],
                                r[3],
                                r[2],
                                r[4],
                            ] for r in results],
                            [None, 2 * cm, 2 * cm, 2 * cm, 2 * cm],
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
                            [None, 2 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(1)
                        )
                    pdf.pagebreak()

                # Panachage
                chart = self.renderer.get_panachage_chart(item, 'pdf')
                if chart:
                    pdf.h2(translate(_('Panachage')))
                    pdf.pdf(chart)
                    pdf.figcaption(translate(_('figcaption_panachage')))
                    pdf.spacer()
                    pdf.pagebreak()

                # Statistics
                summarize = item.results.count() != 1

                pdf.h2(translate(_('Election statistics')))
                if not summarize:
                    res = item.results.first()
                    pdf.table(
                        [[
                            translate(_('Turnout')),
                            '{0:.2f} %'.format(res.turnout)
                        ], [
                            translate(_('eligible Voters')),
                            res.eligible_voters
                        ], [
                            translate(_('Accounted Votes')),
                            res.accounted_votes
                        ], [
                            translate(_('Received Ballots')),
                            res.received_ballots or '0'
                        ], [
                            translate(_('Accounted Ballots')),
                            res.accounted_ballots or '0'
                        ], [
                            translate(_('Blank Ballots')),
                            res.blank_ballots or '0'
                        ], [
                            translate(_('Invalid Ballots')),
                            res.invalid_ballots or '0']
                        ],
                        'even'
                    )

                elif not principal.has_districts:
                    pdf.table(
                        [[
                            translate(principal.label('entity')),
                            translate(_('Turnout')),
                            translate(_('eligible Voters')),
                            translate(_('Accounted Votes')),
                        ]] + [[
                            format_name(result),
                            '{0:.2f} %'.format(result.turnout),
                            result.eligible_voters,
                            result.accounted_votes,
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            '{0:.2f} %'.format(item.turnout),
                            item.eligible_voters,
                            item.accounted_votes,
                        ]],
                        [None, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(principal.label('entity')),
                            translate(_('Received Ballots')),
                            translate(_('Accounted Ballots')),
                            translate(_('Blank Ballots')),
                            translate(_('Invalid Ballots')),

                        ]] + [[
                            format_name(result),
                            result.received_ballots or '0',
                            result.accounted_ballots or '0',
                            result.blank_ballots or '0',
                            result.invalid_ballots or '0',
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            item.received_ballots or '0',
                            item.accounted_ballots or '0',
                            item.blank_ballots or '0',
                            item.invalid_ballots or '0',
                        ]],
                        [None, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )

                else:
                    pdf.table(
                        [[
                            translate(principal.label('entity')),
                            translate(principal.label('district')),
                            translate(_('Turnout')),
                            translate(_('eligible Voters')),
                            translate(_('Accounted Votes')),
                        ]] + [[
                            format_name(result),
                            result.district,
                            '{0:.2f} %'.format(result.turnout),
                            result.eligible_voters,
                            result.accounted_votes,
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            '',
                            '{0:.2f} %'.format(item.turnout),
                            item.eligible_voters,
                            item.accounted_votes,
                        ]],
                        [None, None, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )
                    pdf.spacer()
                    pdf.table(
                        [[
                            translate(principal.label('entity')),
                            translate(principal.label('district')),
                            translate(_('Received Ballots')),
                            translate(_('Accounted Ballots')),
                            translate(_('Blank Ballots')),
                            translate(_('Invalid Ballots')),

                        ]] + [[
                            format_name(result),
                            result.district,
                            result.received_ballots or '0',
                            result.accounted_ballots or '0',
                            result.blank_ballots or '0',
                            result.invalid_ballots or '0',
                        ] for result in item.results] + [[
                            translate(_('Total')),
                            '',
                            item.received_ballots or '0',
                            item.accounted_ballots or '0',
                            item.blank_ballots or '0',
                            item.invalid_ballots or '0',
                        ]],
                        [None, None, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm],
                        style=table_style_results(1)
                    )
                pdf.pagebreak()

            elif isinstance(item, Vote):
                summarize = item.proposal.results.count() != 1

                # Answer
                answer = _('Rejected')
                if item.answer == 'accepted':
                    answer = _('Accepted')
                if item.type == 'complex':
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
                if item.type == 'complex':
                    ballots = (
                        (_('Proposal'), item.proposal),
                        (_('Counter Proposal'), item.counter_proposal),
                        (_('Tie-Breaker'), item.tie_breaker),
                    )
                for title, ballot in ballots:
                    if title:
                        detail = ballot.get_title(locale, self.default_locale)
                        if detail:
                            pdf.h2('{}: {}'.format(translate(title), detail))
                        else:
                            pdf.h2(translate(title))

                    # Factoids
                    pdf.table(
                        [
                            [
                                translate(_('turnout_vote')),
                                translate(_('eligible_voters_vote')),
                                translate(_('Cast Ballots')),
                            ], [
                                '{0:.2f}%'.format(ballot.turnout),
                                ballot.eligible_voters,
                                ballot.cast_ballots,
                            ]
                        ],
                        'even',
                        style=table_style_factoids
                    )
                    pdf.spacer()

                    # Results
                    if not summarize:
                        res = ballot.results.first()
                        pdf.table(
                            [[
                                translate(_('Yes %')).replace('%', '').strip(),
                                translate(_('No %')).replace('%', '').strip(),
                                '{} / {}'.format(
                                    translate(_('Empty')),
                                    translate(_('Invalid'))
                                ),
                            ], [
                                '{} / {:.2f}%'.format(
                                    res.yeas or '0',
                                    res.yeas_percentage
                                ),
                                '{} / {:.2f}%'.format(
                                    res.nays or '0',
                                    res.nays_percentage
                                ),
                                '{} / {}'.format(
                                    res.empty or '0',
                                    res.invalid or '0',
                                )
                            ]],
                            'even',
                            style=table_style_factoids
                        )
                        pdf.spacer()

                    elif not principal.has_districts:
                        pdf.spacer()
                        pdf.table(
                            [[
                                translate(principal.label('entity')),
                                translate(_('Result')),
                                translate(_('Yes %')),
                                translate(_('No %')),
                            ]] + [[
                                format_name(result),
                                translate(_('Accepted')) if result.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(result.yeas_percentage),
                                '{0:.2f}%'.format(result.nays_percentage),
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                translate(_('Accepted')) if ballot.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(ballot.yeas_percentage),
                                '{0:.2f}%'.format(ballot.nays_percentage),
                            ]],
                            [None, 2.3 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(2)
                        )
                        pdf.pagebreak()
                        pdf.table(
                            [[
                                translate(principal.label('entity')),
                                translate(_('Empty')),
                                translate(_('Invalid')),
                                translate(_('Yes %')).replace('%', '').strip(),
                                translate(_('No %')).replace('%', '').strip(),
                            ]] + [[
                                format_name(result),
                                result.empty or '0',
                                result.invalid or '0',
                                result.yeas or '0',
                                result.nays or '0',
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                ballot.empty or '0',
                                ballot.invalid or '0',
                                ballot.yeas or '0',
                                ballot.nays or '0',
                            ]],
                            [None, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm],
                            style=table_style_results(1)
                        )

                    else:
                        pdf.spacer()
                        pdf.table(
                            [[
                                translate(principal.label('entity')),
                                translate(principal.label('district')),
                                translate(_('Result')),
                                translate(_('Yes %')),
                                translate(_('No %')),
                            ]] + [[
                                format_name(result),
                                result.district,
                                translate(_('Accepted')) if result.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(result.yeas_percentage),
                                '{0:.2f}%'.format(result.nays_percentage),
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                '',
                                translate(_('Accepted')) if ballot.accepted
                                else translate(_('Rejected')),
                                '{0:.2f}%'.format(ballot.yeas_percentage),
                                '{0:.2f}%'.format(ballot.nays_percentage),
                            ]],
                            [None, None, 2.3 * cm, 2 * cm, 2 * cm],
                            style=table_style_results(2)
                        )
                        pdf.pagebreak()
                        pdf.table(
                            [[
                                translate(principal.label('entity')),
                                translate(principal.label('district')),
                                translate(_('Empty')),
                                translate(_('Invalid')),
                                translate(_('Yes %')).replace('%', '').strip(),
                                translate(_('No %')).replace('%', '').strip(),
                            ]] + [[
                                format_name(result),
                                result.district,
                                result.empty or '0',
                                result.invalid or '0',
                                result.yeas or '0',
                                result.nays or '0',
                            ] for result in ballot.results] + [[
                                translate(_('Total')),
                                '',
                                ballot.empty or '0',
                                ballot.invalid or '0',
                                ballot.yeas or '0',
                                ballot.nays or '0',
                            ]],
                            [
                                None,
                                None,
                                2.3 * cm,
                                2.3 * cm,
                                2.0 * cm,
                                2.0 * cm
                            ],
                            style=table_style_results(1)
                        )

                    # Map
                    if principal.is_year_available(item.date.year):
                        pdf.pagebreak()
                        pdf.pdf(
                            self.renderer.get_map_chart(ballot, 'pdf', locale),
                            0.8
                        )
                        pdf.pagebreak()
                    else:
                        pdf.spacer()

            # Add related link
            link = item.related_link
            if link:
                pdf.h2(translate(_('Related link')))
                pdf.p_markup('<a href="{link}">{link}</a>'.format(link=link))

            pdf.generate()

    def create_pdfs(self):
        """ Generates all PDFs for the given application.

        Only generates PDFs if not already generated since the last change of
        the election or vote.

        Optionally cleans up unused PDFs.

        """

        # Get all elections and votes
        items = self.session.query(Election).all()
        items.extend(self.session.query(Vote).all())

        # Read existing PDFs
        fs = self.app.filestorage
        if not fs.exists(self.pdf_dir):
            fs.makedir(self.pdf_dir)
        existing = fs.listdir(self.pdf_dir)

        # Generate the PDFs
        for locale in self.app.locales:
            for item in items:
                filename = pdf_filename(item, locale)
                if filename not in existing and item.completed:
                    path = '{}/{}'.format(self.pdf_dir, filename)
                    if fs.exists(path):
                        fs.remove(path)
                    try:
                        self.generate_pdf(item, path, locale)
                        self.sign_pdf(path)
                        log.info("{} created".format(filename))
                    except Exception as ex:
                        # Don't leave probably broken PDFs laying around
                        if fs.exists(path):
                            fs.remove(path)
                        raise ex

        # Delete old PDFs
        existing = fs.listdir(self.pdf_dir)
        existing = dict(groupbylist(
            sorted(existing),
            key=lambda a: a.split('.')[0]
        ))

        # ... orphaned files
        created = [
            pdf_filename(item, '').split('.')[0] for item in items
        ]
        for id in set(existing.keys()) - set(created):
            self.remove(self.pdf_dir, existing[id])

        # ... old files
        for files in existing.values():
            files = sorted(files, reverse=True)
            self.remove(self.pdf_dir, files[len(self.app.locales):])

from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day import _
from onegov.election_day import log
from onegov.election_day.pdf import Pdf
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils.d3_renderer import D3Renderer
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_connection_results
from onegov.election_day.utils.election_compound import \
    get_candidate_statistics
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_superregions
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_deltas
from onegov.pdf import LexworkSigner
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
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
        self.renderer = renderer or D3Renderer(app)

    def remove(self, directory, files):
        """ Safely removes the given files from the directory. """
        if not files:
            return

        fs = self.app.filestorage
        for file in files:
            path = '{}/{}'.format(directory, file)
            if fs.exists(path) and not fs.isdir(path):
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

        old_locale = item.session_manager.current_locale
        item.session_manager.current_locale = locale

        with self.app.filestorage.open(path, 'wb') as f:

            pdf = Pdf(
                f,
                title=item.title,
                author=principal.name,
                locale=locale,
                translations=self.app.translations
            )
            pdf.init_a4_portrait(
                page_fn=page_fn_footer,
                page_fn_later=page_fn_header_and_footer
            )

            # Add Header
            pdf.h1(item.title)

            # Add dates
            changed = item.last_result_change
            if getattr(changed, 'tzinfo', None) is not None:
                tz = timezone('Europe/Zurich')
                changed = tz.normalize(changed.astimezone(tz))
            pdf.dates_line(item.date, changed)
            pdf.spacer()

            if isinstance(item, Election) and item.tacit:
                self.add_tacit_election(principal, item, pdf)

            elif isinstance(item, Election):
                self.add_election(principal, item, pdf)

            elif isinstance(item, ElectionCompound):
                self.add_election_compound(principal, item, pdf)

            elif isinstance(item, Vote):
                self.add_vote(principal, item, pdf, locale)

            # Add related link
            link = item.related_link
            if link:
                pdf.h2(_('Related link'))
                pdf.p_markup('<a href="{link}">{link}</a>'.format(link=link))

            pdf.generate()

        item.session_manager.current_locale = old_locale

    def add_tacit_election(self, principal, election, pdf):

        # Candidates
        data = get_candidates_data(election)
        if data and data.get('results'):
            pdf.h2(_('Candidates'))
            pdf.spacer()
            pdf.results(
                head=[
                    _('Candidate'),
                    _('Party'),
                    _('List'),
                    _('Elected'),
                ],
                body=[
                    [
                        '{} {}'.format(r[0], r[1]),
                        r[3],
                        r[5],
                        pdf.translate(_('Yes')) if r[2] else '',
                    ]
                    for r in get_candidates_results(election, self.session)
                ],
                hide=[
                    False,
                    election.type != 'majorz',
                    election.type == 'majorz',
                    False
                ],
            )
            pdf.pagebreak()

    def add_election(self, principal, election, pdf):

        def format_name(item):
            return item.name if item.entity_id else pdf.translate(_("Expats"))

        majorz = election.type == 'majorz'
        show_majority = majorz and election.majority_type == 'absolute'

        # Factoids
        pdf.factoids(
            [_('Turnout'), _('eligible Voters'), _('Received Ballots')],
            [
                '{0:.2f}%'.format(election.turnout),
                election.eligible_voters,
                election.received_ballots,
            ]
        )
        pdf.spacer()
        pdf.factoids(
            [
                _('Seats') if majorz else principal.label('mandates'),
                _('Absolute majority') if show_majority else '',
                ''
            ],
            [
                election.allocated_mandates,
                election.absolute_majority if show_majority else '',
                ''
            ],
        )
        pdf.spacer()
        pdf.spacer()

        # Lists
        chart, data = self.renderer.get_lists_chart(election, 'pdf', True)
        if data and data.get('results'):
            pdf.h2(_('Lists'))
            pdf.pdf(chart)
            pdf.spacer()
            pdf.results(
                head=[
                    _('List'),
                    principal.label('mandates'),
                    _('single_votes')
                ],
                body=[
                    [
                        r['text'],
                        r['value2'],
                        r['value']
                    ]
                    for r in data['results']
                ],
            )
            pdf.pagebreak()

        # Candidates
        chart = self.renderer.get_candidates_chart(election, 'pdf')
        if chart:
            pdf.h2(_('Candidates'))
            pdf.pdf(chart)
            pdf.spacer()
            pdf.results(
                head=[
                    _('Candidate'),
                    _('Party'),
                    _('List'),
                    _('Elected'),
                    _('single_votes')
                ],
                body=[
                    [
                        '{} {}'.format(r.family_name, r.first_name),
                        r.party,
                        r.list_name,
                        pdf.translate(_('Yes')) if r.elected else '',
                        r.votes
                    ]
                    for r in get_candidates_results(election, self.session)
                ],
                hide=[
                    False,
                    not majorz,
                    majorz,
                    False,
                    False
                ],
            )
            pdf.pagebreak()

        # Connections
        chart = self.renderer.get_connections_chart(election, 'pdf')
        if chart:
            pdf.h2(_('List connections'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_connections'))
            pdf.spacer()

            connections = get_connection_results(election, self.session)
            spacers = []
            table = [[
                '{} / {} / {}'.format(
                    pdf.translate(_('List connection')),
                    pdf.translate(_('Sublist connection')),
                    pdf.translate(_('Party'))
                ),
                pdf.translate(_('single_votes'))
            ]]
            for connection in connections:
                table += [[
                    MarkupParagraph('{} {}'.format(
                        pdf.translate(_('List connection')),
                        connection[0]
                    ), pdf.style.indent_0),
                    connection[1]
                ]]
                for sc in connection[3]:
                    table += [[
                        MarkupParagraph('{} {}'.format(
                            pdf.translate(_('Sublist connection')),
                            sc[0]
                        ), pdf.style.indent_1),
                        sc[1]
                    ]]
                    table += [[
                        MarkupParagraph(l[0], pdf.style.indent_2),
                        l[1]
                    ] for l in sc[2]]
                table += [[
                    MarkupParagraph(l[0], pdf.style.indent_1),
                    l[1]
                ] for l in connection[2]]
                spacers.append(len(table))

            pdf.table(
                table,
                [None, 2 * cm, 2 * cm],
                style=pdf.style.table_results + tuple([
                    ('TOPPADDING', (0, row), (-1, row), 15)
                    for row in spacers[:-1]
                ])
            )
            pdf.pagebreak()

        # Party Strengths
        chart = self.renderer.get_party_strengths_chart(
            election, 'pdf'
        )
        if chart:
            pdf.h2(_('Party strengths'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_party_strengths'))
            pdf.spacer()
            years, parties = get_party_results(election)
            deltas, results = get_party_results_deltas(
                election, years, parties
            )
            results = results[sorted(results.keys())[-1]]
            pdf.results(
                head=[
                    _('Party'),
                    principal.label('mandates'),
                    _('single_votes'),
                    _('single_votes'),
                    'Δ {}'.format(years[0]),
                ],
                body=[
                    [
                        r[0],
                        r[1],
                        r[3],
                        r[2],
                        r[4] if deltas else 0,
                    ]
                    for r in results
                ],
                hide=[
                    False,
                    False,
                    False,
                    False,
                    not deltas
                ],
            )
            pdf.pagebreak()

        # Parties Panachage
        chart = self.renderer.get_parties_panachage_chart(election, 'pdf')
        if chart:
            pdf.h2(_('Panachage (parties)'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_panachage'))
            pdf.spacer()
            pdf.pagebreak()

        # Lists Panachage
        chart = self.renderer.get_lists_panachage_chart(election, 'pdf')
        if chart:
            pdf.h2(_('Panachage (lists)'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_panachage'))
            pdf.spacer()
            pdf.pagebreak()

        # Statistics
        pdf.h2(_('Election statistics'))
        hide_districts = (
            not principal.has_districts
            or election.domain in (
                'region', 'district', 'municipality', 'none'
            )
        )
        pdf.results(
            head=[
                principal.label('entity'),
                principal.label('district'),
                _('Turnout'),
                _('eligible Voters'),
                _('Expats'),
                _('Accounted Votes'),
            ],
            body=[
                [
                    format_name(result),
                    result.district,
                    '{0:.2f} %'.format(result.turnout),
                    result.eligible_voters,
                    result.expats,
                    result.accounted_votes,
                ]
                for result in election.results
            ],
            foot=[
                pdf.translate(_('Total')),
                '',
                '{0:.2f} %'.format(election.turnout),
                election.eligible_voters,
                election.expats,
                election.accounted_votes,
            ],
            hide=[
                False,
                hide_districts,
                False,
                False,
                not election.expats,
                False
            ],
        )
        pdf.spacer()
        pdf.results(
            head=[
                principal.label('entity'),
                principal.label('district'),
                _('Received Ballots'),
                _('Accounted Ballots'),
                _('Blank Ballots'),
                _('Invalid Ballots'),
            ],
            body=[
                [
                    format_name(result),
                    result.district,
                    result.received_ballots or '0',
                    result.accounted_ballots or '0',
                    result.blank_ballots or '0',
                    result.invalid_ballots or '0',
                ]
                for result in election.results
            ],
            foot=[
                pdf.translate(_('Total')),
                '',
                election.received_ballots or '0',
                election.accounted_ballots or '0',
                election.blank_ballots or '0',
                election.invalid_ballots or '0',
            ],
            hide=[
                False,
                hide_districts,
                False,
                False,
                False,
                False
            ],
        )
        pdf.pagebreak()

    def add_election_compound(self, principal, compound, pdf):

        def label(value):
            if value == 'district':
                if compound.domain_elections == 'region':
                    return principal.label('region')
                if compound.domain_elections == 'municipality':
                    return _("Municipality")
            if value == 'districts':
                if compound.domain_elections == 'region':
                    return principal.label('regions')
                if compound.domain_elections == 'municipality':
                    return _("Municipalities")
            return principal.label(value)

        def format_gender(value):
            result = _('undetermined')
            if value == 'female':
                result = _('female')
            if value == 'male':
                result = _('male')
            return pdf.translate(result)

        districts = {
            election.id: (
                election.domain_segment,
                election.domain_supersegment
            )
            for election in compound.elections if election.results.first()
        }

        has_superregions = (
            principal.has_superregions
            and compound.domain_elections == 'region'
        )

        # Factoids
        pdf.factoids(
            [label('mandates'), '', ''],
            [compound.allocated_mandates, '', '']
        )
        pdf.spacer()
        pdf.spacer()

        # Seat allocation
        chart = self.renderer.get_seat_allocation_chart(compound, 'pdf')
        if compound.show_seat_allocation and chart:
            pdf.h2(_('Seat allocation'))
            pdf.pdf(chart)
            pdf.spacer()
            years, parties = get_party_results(compound)
            years = years[:2]
            if years:
                current_year = years[-1]
                pdf.results(
                    head=[
                        _('Party'),
                        *years,
                    ],
                    body=[
                        [
                            parties[party][current_year]['name'],
                            *[
                                parties[party][year]['mandates'] or '0'
                                for year in years
                            ]
                        ]
                        for party in parties
                    ],
                )
            pdf.pagebreak()

        # Superregions
        if has_superregions:
            superregions = get_superregions(compound, principal)
            if superregions:
                pdf.h2(label('superregions'))
                pdf.results(
                    head=[
                        label('superregion'),
                        label('mandates')
                    ],
                    body=[
                        [
                            name,
                            values['mandates']['allocated']
                        ]
                        for name, values in superregions.items()
                    ],
                )
                pdf.pagebreak()

        # Districts
        pdf.h2(label('districts'))
        pdf.results(
            head=[
                label('district'),
                label('superregion'),
                label('mandates')
            ],
            body=[
                [
                    e.domain_segment,
                    districts.get(e.id, ('', ''))[1],
                    e.allocated_mandates
                ]
                for e in compound.elections
            ],
            hide=[
                False,
                not has_superregions,
                False
            ],
        )
        pdf.pagebreak()

        # Elected candidates
        elected_candidates = get_elected_candidates(compound, self.session)
        pdf.h2(_('Elected candidates'))
        pdf.spacer()
        pdf.results(
            head=[
                _('Candidate'),
                _('List'),
                label('superregion'),
                label('district'),
            ],
            body=[
                [
                    '{} {}'.format(r.family_name, r.first_name),
                    r.list,
                    districts.get(r.election_id, ('', ''))[1],
                    districts.get(r.election_id, ('', ''))[0],
                ]
                for r in elected_candidates
            ],
            hide=[
                False,
                False,
                not has_superregions,
                False
            ],
        )
        pdf.pagebreak()

        # List groups
        chart = self.renderer.get_list_groups_chart(compound, 'pdf')
        if compound.show_list_groups and chart:
            pdf.h2(_('List groups'))
            pdf.pdf(chart)
            pdf.figcaption('<b>{}</b>: {}'.format(
                pdf.translate(_('Voters count')),
                pdf.translate(_('figcaption_party_strengths'))
            ))
            pdf.spacer()
            pdf.results(
                head=[
                    _('List group'),
                    _('Voters count'),
                    label('mandates'),
                ],
                body=[
                    [
                        r.name,
                        r.voters_count,
                        r.number_of_mandates
                    ]
                    for r in get_list_groups(compound)
                ],
            )
            pdf.pagebreak()

        # Parties
        chart = self.renderer.get_party_strengths_chart(compound, 'pdf')
        if compound.show_party_strengths and chart:
            pdf.h2(_('Party strengths'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_party_strengths'))
            pdf.spacer()
            years, parties = get_party_results(compound)
            deltas, results = get_party_results_deltas(
                compound, years, parties
            )
            if results:
                results = results[sorted(results.keys())[-1]]
                pdf.results(
                    head=[
                        _('Party'),
                        label('mandates'),
                        _('single_votes'),
                        _('single_votes'),
                        'Δ {}'.format(years[0]),
                    ],
                    body=[
                        [
                            r[0],
                            r[1],
                            r[3],
                            r[2],
                            r[4] if deltas else 0,
                        ]
                        for r in results
                    ],
                    hide=[
                        False,
                        False,
                        False,
                        False,
                        not deltas
                    ],
                )
            pdf.pagebreak()

        # Parties Panachage
        chart = self.renderer.get_parties_panachage_chart(compound, 'pdf')
        if compound.show_party_panachage and chart:
            pdf.h2(_('Panachage (parties)'))
            pdf.pdf(chart)
            pdf.figcaption(_('figcaption_panachage'))
            pdf.spacer()
            pdf.pagebreak()

        # Statistics
        pdf.h2(_('Election statistics'))
        results = compound.results
        pdf.results(
            head=[
                label('district'),
                label('superregion'),
                _('eligible Voters'),
                _('Expats'),
                _('Turnout'),
                _('Accounted Votes'),
            ],
            body=[
                [
                    result.domain_segment,
                    result.domain_supersegment,
                    result.eligible_voters,
                    result.expats,
                    '{0:.2f} %'.format(result.turnout),
                    result.accounted_votes,
                ]
                for result in results
            ],
            hide=[
                False,
                not has_superregions,
                False,
                not sum([result.expats for result in results]),
                False,
                False
            ],
        )
        pdf.spacer()
        pdf.results(
            head=[
                label('district'),
                label('superregion'),
                _('Received Ballots'),
                _('Accounted Ballots'),
                _('Blank Ballots'),
                _('Invalid Ballots'),
            ],
            body=[
                [
                    result.domain_segment,
                    result.domain_supersegment,
                    result.received_ballots or '0',
                    result.accounted_ballots or '0',
                    result.blank_ballots or '0',
                    result.invalid_ballots or '0',
                ] for result in results
            ],
            hide=[
                False,
                not has_superregions,
                False,
                False,
                False,
                False
            ],
        )

        candidate_statistics = get_candidate_statistics(
            compound, elected_candidates
        )
        if candidate_statistics:
            pdf.spacer()
            pdf.results(
                head=[
                    _('Elected candidates'),
                    _('Count'),
                    _('Average age'),
                ],
                body=[
                    [
                        format_gender(gender),
                        candidate_statistics[gender]['count'],
                        candidate_statistics[gender]['age'],
                    ]
                    for gender in sorted(candidate_statistics)
                    if gender != 'total'
                ],
                foot=[
                    _('Total'),
                    candidate_statistics['total']['count'],
                    candidate_statistics['total']['age'],
                ]
            )
        pdf.pagebreak()

    def add_vote(self, principal, vote, pdf, locale):
        completed = vote.completed
        nan = '-'

        def format_name(item):
            if hasattr(item, 'entity_id'):
                if item.entity_id:
                    return item.name
            if item.name:
                return item.name
            return pdf.translate(_("Expats"))

        def format_accepted(result):
            accepted = result.accepted
            if accepted is None:
                return _('Intermediate results abbrev')
            return accepted and _('Accepted') or _('Rejected')

        def format_percentage(number):
            return '{0:.2f}%'.format(number)

        def format_value(result, attr, fmt=format_percentage):
            if result.accepted is None:
                return nan
            return fmt(getattr(result, attr))

        # Answer
        answer = _('Rejected')

        if not completed:
            counted, total = vote.progress
            answer = _(
                'Intermediate results: ${counted} of ${total} ${entities}',
                mapping={
                    'total': total,
                    'counted': counted,
                    'entities': pdf.translate(principal.label('entities'))
                }
            )
        else:
            if vote.answer == 'accepted':
                answer = _('Accepted')
            if vote.type == 'complex':
                proposal = vote.proposal.accepted
                counter_proposal = vote.counter_proposal.accepted
                if not proposal and not counter_proposal:
                    answer = _('Proposal and counter proposal rejected')
                if proposal and not counter_proposal:
                    answer = _('Proposal accepted')
                if not proposal and counter_proposal:
                    answer = _('Counter proposal accepted')
                if proposal and counter_proposal:
                    if vote.tie_breaker.accepted:
                        answer = _('Tie breaker in favor of the proposal')
                    else:
                        answer = _(
                            'Tie breaker in favor of the counter proposal'
                        )
        pdf.p(pdf.translate(answer))
        pdf.spacer()

        ballots = ((None, vote.proposal),)
        if vote.type == 'complex':
            ballots = (
                (_('Proposal'), vote.proposal),
                (_('Counter Proposal'), vote.counter_proposal),
                (_('Tie-Breaker'), vote.tie_breaker),
            )
        for title, ballot in ballots:
            # Ballot title
            subtitle = pdf.h2
            if title:
                subtitle = pdf.h3
                detail = ballot.title
                if detail:
                    pdf.h2('{}: {}'.format(pdf.translate(title), detail))
                else:
                    pdf.h2(title)

            # Factoids
            if completed:
                pdf.factoids(
                    [
                        _('turnout_vote'),
                        _('eligible_voters_vote'),
                        _('Cast Ballots')
                    ],
                    [
                        '{0:.2f}%'.format(ballot.turnout),
                        ballot.eligible_voters,
                        ballot.cast_ballots,
                    ]
                )
                pdf.spacer()
                pdf.spacer()

            # Entities
            subtitle(principal.label('entities'))
            pdf.spacer()

            pdf.results(
                head=[
                    principal.label('entity'),
                    principal.label('district'),
                    _('Result'),
                    _('Yes %'),
                    _('No %'),
                ],
                body=[
                    [
                        format_name(result),
                        result.district,
                        pdf.translate(format_accepted(result)),
                        format_value(result, 'yeas_percentage'),
                        format_value(result, 'nays_percentage'),
                    ]
                    for result in ballot.results
                ],
                foot=[
                    pdf.translate(_('Total')),
                    '',
                    pdf.translate(format_accepted(ballot)),
                    format_value(ballot, 'yeas_percentage'),
                    format_value(ballot, 'nays_percentage'),
                ],
                hide=[
                    False,
                    not principal.has_districts,
                    False,
                    False,
                    False,
                ],
            )
            pdf.pagebreak()

            if principal.is_year_available(vote.date.year):
                pdf.pdf(
                    self.renderer.get_entities_map(ballot, 'pdf', locale),
                    0.8
                )
                pdf.pagebreak()

            # Districts
            if principal.has_districts:
                subtitle(principal.label('districts'))
                pdf.spacer()
                pdf.results(
                    head=[
                        principal.label('district'),
                        _('Result'),
                        _('Yes %'),
                        _('No %'),
                    ],
                    body=[
                        [
                            format_name(result),
                            pdf.translate(format_accepted(result)),
                            format_value(result, 'yeas_percentage'),
                            format_value(result, 'nays_percentage'),
                        ]
                        for result in ballot.results_by_district
                    ],
                    foot=[
                        pdf.translate(_('Total')),
                        pdf.translate(format_accepted(ballot)),
                        format_value(ballot, 'yeas_percentage'),
                        format_value(ballot, 'nays_percentage'),
                    ],
                )
                pdf.pagebreak()
                if principal.is_year_available(vote.date.year):
                    pdf.pdf(
                        self.renderer.get_districts_map(
                            ballot, 'pdf', locale
                        ),
                        0.8
                    )
                    pdf.pagebreak()

            # Statistics
            subtitle(_('Statistics'))
            pdf.spacer()
            pdf.results(
                head=[
                    principal.label('entity'),
                    principal.label('district'),
                    _('eligible_voters_vote'),
                    _('Expats'),
                    _('Cast Ballots'),
                    _('turnout_vote'),
                ],
                body=[
                    [
                        format_name(result),
                        result.district,
                        result.eligible_voters or '0',
                        result.expats,
                        result.cast_ballots or '0',
                        '{0:.2f} %'.format(result.turnout),
                    ]
                    for result in ballot.results
                ],
                foot=[
                    pdf.translate(_('Total')),
                    '',
                    ballot.eligible_voters or '0',
                    ballot.expats,
                    ballot.cast_ballots or '0',
                    '{0:.2f} %'.format(ballot.turnout),
                ],
                hide=[
                    False,
                    not principal.has_districts,
                    False,
                    not ballot.expats,
                    False,
                    False,
                ],
            )
            pdf.spacer()
            pdf.results(
                head=[
                    principal.label('entity'),
                    principal.label('district'),
                    _('Empty votes'),
                    _('Invalid votes'),
                    pdf.translate(_('Yeas')).replace('-', '- '),
                    pdf.translate(_('Nays')).replace('-', '- '),
                ],
                body=[
                    [
                        format_name(result),
                        result.district,
                        result.empty or '0',
                        result.invalid or '0',
                        result.yeas or '0',
                        result.nays or '0',
                    ]
                    for result in ballot.results
                ],
                foot=[
                    pdf.translate(_('Total')),
                    '',
                    ballot.empty or '0',
                    ballot.invalid or '0',
                    ballot.yeas or '0',
                    ballot.nays or '0',
                ],
                hide=[
                    False,
                    not principal.has_districts,
                    False,
                    False,
                    False,
                    False,
                ],
            )

            pdf.pagebreak()

    def create_pdfs(self):
        """ Generates all PDFs for the given application.

        Only generates PDFs if not already generated since the last change of
        the election, election compound or vote.

        Cleans up unused files.

        """

        publish = self.app.principal.publish_intermediate_results

        def render_item(item):
            if item.completed:
                return True
            counted, total = item.progress
            if counted == 0:
                return False
            if not publish:
                return False
            if isinstance(item, Vote) and publish.get('vote'):
                return True
            return False

        # Get all elections and votes
        items = self.session.query(Election).all()
        items.extend(self.session.query(ElectionCompound).all())
        items.extend(self.session.query(Vote).all())

        # Read existing PDFs
        fs = self.app.filestorage
        if not fs.exists(self.pdf_dir):
            fs.makedir(self.pdf_dir)
        existing = fs.listdir(self.pdf_dir)

        # Generate the PDFs
        created = 0
        filenames = []
        for locale in sorted(self.app.locales):
            for item in items:
                filename = pdf_filename(item, locale)
                filenames.append(filename)
                if filename not in existing and render_item(item):
                    created += 1
                    path = '{}/{}'.format(self.pdf_dir, filename)
                    if fs.exists(path):
                        fs.remove(path)
                    try:
                        self.generate_pdf(item, path, locale)
                        self.sign_pdf(path)
                        log.info("{} created".format(filename))
                    except Exception:
                        log.exception("Could not create {} ({})".format(
                            filename, item.title
                        ))
                        # Don't leave probably broken PDFs laying around
                        if fs.exists(path):
                            fs.remove(path)

        # Delete obsolete PDFs
        obsolete = set(existing) - set(filenames)
        self.remove(self.pdf_dir, obsolete)

        return created, len(obsolete)

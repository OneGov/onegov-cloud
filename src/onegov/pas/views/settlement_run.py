from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import SettlementRunCollection,\
    AttendenceCollection, CommissionCollection
from onegov.pas.forms import SettlementRunForm
from onegov.pas.layouts import SettlementRunCollectionLayout
from onegov.pas.layouts import SettlementRunLayout
from onegov.pas.models import (
    SettlementRun,
    Party,
    RateSet,
    Commission,
)
from webob import Response
from sqlalchemy import or_
from decimal import Decimal
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration)
from onegov.pas.models.attendence import TYPES, Attendence
from onegov.pas.path import SettlementRunExport, SettlementRunAllExport
from onegov.pas.models import Parliamentarian


from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from datetime import date


PDF_CSS = """
@page {
    size: A4;
    margin: 2.5cm 0.75cm 2cm 0.75cm;  /* top right bottom left */
    @top-right {
        content: "Staatskanzlei";
        font-family: Helvetica, Arial, sans-serif;
        font-size: 8pt;
    }
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 7pt;
    line-height: 1.2;
}

table {
    border-collapse: collapse;
    margin-top: 1cm;
    width: 100%;
    table-layout: fixed;
}

/* Journal entries table */
.journal-table th:nth-child(1), /* Date */
.journal-table td:nth-child(1) {
    width: 20pt;
}

.journal-table th:nth-child(2), /* Person */
.journal-table td:nth-child(2) {
    width: 100pt;
}

.journal-table th:nth-child(3), /* Type */
.journal-table td:nth-child(3) {
    width: 170pt;
}

.journal-table th:nth-child(4), /* Value */
.journal-table td:nth-child(4),
.journal-table th:nth-child(5), /* CHF */
.journal-table td:nth-child(5),
.journal-table th:nth-child(6), /* CHF + TZ */
.journal-table td:nth-child(6) {
    width: 30pt;
}

/* Party summary table */
.summary-table th:nth-child(1), /* Name */
.summary-table td:nth-child(1) {
    width: 120pt;
}

.summary-table th:nth-child(2), /* Meetings */
.summary-table td:nth-child(2),
.summary-table th:nth-child(3), /* Expenses */
.summary-table td:nth-child(3),
.summary-table th:nth-child(4), /* Total */
.summary-table td:nth-child(4),
.summary-table th:nth-child(5), /* COLA */
.summary-table td:nth-child(5),
.summary-table th:nth-child(6), /* Final */
.summary-table td:nth-child(6) {
    width: 60pt;
}

/* Dark header for title row */
th[colspan="6"] {
    background-color: #707070;
    color: white;
    font-weight: bold;
    text-align: left;
    padding: 2pt;
    border: 1pt solid #000;
}

th:not([colspan]) {
    background-color: #d5d7d9;
    font-weight: bold;
    text-align: left;
    padding: 2pt;
    border: 1pt solid #000;
}

td {
    padding: 2pt;
    border: 1pt solid #000;
}

tr:nth-child(even):not(.total-row) td {
    background-color: #f3f3f3;
}

.numeric {
    text-align: right;
}

.total-row {
    font-weight: bold;
    background-color: #d5d7d9;
}

.summary-table {
    margin-top: 2cm;
    page-break-before: always;
}
    """


@PasApp.html(
    model=SettlementRunCollection,
    template='settlement_runs.pt',
    permission=Private
)
def view_settlement_runs(
    self: SettlementRunCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = SettlementRunCollectionLayout(self, request)

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'settlement_runs': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=SettlementRunCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=SettlementRunForm
)
def add_settlement_run(
    self: SettlementRunCollection,
    request: 'TownRequest',
    form: SettlementRunForm
) -> 'RenderData | Response':

    if form.submitted(request):
        settlement_run = self.add(**form.get_useful_data())
        request.success(_('Added a new settlement run'))

        return request.redirect(request.link(settlement_run))

    layout = SettlementRunCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New settlement run'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=SettlementRun,
    template='settlement_run.pt',
    permission=Private
)
def view_settlement_run(
    self: SettlementRun,
    request: 'TownRequest'
) -> 'RenderData':
    """ A page where all exports are listed and grouped by category. """
    layout = SettlementRunLayout(self, request)

    # Get parties active during settlement run period
    parties = request.session.query(Party).filter(
        or_(
            Party.end.is_(None),
            Party.end >= self.start
        ),
        Party.start <= self.end
    ).order_by(Party.name)

    # Get commissions active during settlement run period
    com = CommissionCollection(request.session)
    commissions = com.query().order_by(Commission.name)

    # Get parliamentarians active during settlement run period
    parliamentarians = [
        p
        for p in request.session.query(Parliamentarian).order_by(
            Parliamentarian.last_name, Parliamentarian.first_name
        )
        if p.active_during(self.start, self.end)
    ]

    categories = {
        'party': {
            'title': _('Settlements by Party'),
            'links': [
                Link(
                    party.title + ' Total',
                    request.link(
                        SettlementRunExport(
                            self,
                            party,
                            category='party'
                        ),
                        'run-export'
                    ),
                    )
                for party in parties
            ],
        },
        'all': {
            'title': _('All Settlements'),  # Gesamtabrechnung
            'links': [
                Link(
                    _('All Parties'),
                    request.link(
                        SettlementRunAllExport(
                            settlement_run=self,
                            category='all-parties'
                        ),
                        name='run-export'
                    ),
                )
            ],
        },
        'commissions': {
            'title': _('Settlements by Commission'),
            'links': [
                Link(
                    commission.title + ' Total',
                    request.link(
                        SettlementRunExport(
                            self,
                            commission,
                            category='commission'
                        ),
                        'run-export'
                    ),
                    )
                for commission in commissions
            ],
        },
        'parliamentarians': {
            'title': _('Settlements by Parliamentarian'),
            'links': [
                Link(
                    f'{p.last_name} {p.first_name}',
                    request.link(
                        SettlementRunExport(
                            self,
                            p,
                            category='parliamentarian'
                        ),
                        'run-export'
                    ),
                )
                for p in parliamentarians
            ],
        },
    }

    return {
        'layout': layout,
        'settlement_run': self,
        'categories': categories,
        'title': layout.title,
    }


def _get_party_totals(
    self: SettlementRun,
    request: 'TownRequest'
) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]]:
    """Get totals grouped by party."""
    session = request.session

    # Get rate set for the year
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == self.start.year)
        .first()
    )

    if not rate_set:
        return []

    # Get all attendences in period
    attendences = AttendenceCollection(
        session,
        date_from=self.start,
        date_to=self.end
    )

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Initialize party totals
    party_totals: dict[str, dict[str, Decimal]] = {}

    # Calculate totals for each party
    for attendence in attendences.query():
        # Get parliamentarian's party
        current_party = None
        for role in attendence.parliamentarian.roles:
            if role.party and (role.end is None or role.end >= self.start):
                current_party = role.party
                break

        if not current_party:
            continue

        party_name = current_party.name

        if party_name not in party_totals:
            # Name Sitzungen Spesen Total Einträge Teuerungszulagen Auszahlung
            party_totals[party_name] = {
                'Meetings': Decimal('0'),
                'Expenses': Decimal('0'),  # Always 0 for now (Spesen)
                'Total': Decimal('0'),  # Expenses + Meetings
                'Cost-of-living Allowance': Decimal('0'),  # Teuerungszulagen
                'Final': Decimal('0')  # Auszahlung
            }

        # Calculate base rate
        is_president = any(r.role == 'president'
                           for r in attendence.parliamentarian.roles)

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            ),
        )

        # Update totals
        party_totals[party_name]['Meetings'] += Decimal(str(base_rate))
        base_total = party_totals[party_name]['Meetings']
        cola_amount = base_total * (cola_multiplier - 1)

        expenses = party_totals[party_name]['Expenses'] + base_total
        party_totals[party_name]['Total'] = base_total + expenses
        party_totals[party_name]['Cost-of-living Allowance'] = cola_amount
        party_totals[party_name]['Final'] = base_total + cola_amount

    # Convert to sorted list of tuples
    result = [
        (
            name,
            data['Meetings'],
            data['Expenses'],
            data['Total'],
            data['Cost-of-living Allowance'],
            data['Final']
        )
        for name, data in sorted(party_totals.items())
    ]

    # Add total row
    totals = (
        Decimal(sum(r[1] for r in result)),  # Sessions
        Decimal(sum(r[2] for r in result)),  # Expenses
        Decimal(sum(r[3] for r in result)),  # Total
        Decimal(sum(r[4] for r in result)),  # COLA
        Decimal(sum(r[5] for r in result)),  # Final
    )

    result.append(('Total Parteien', *totals))

    return result


def generate_parliamentarian_settlement_pdf(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    parliamentarian: Parliamentarian,
) -> bytes:
    """Generate PDF for parliamentarian settlement data."""
    font_config = FontConfiguration()
    css = CSS(string="""
        @page {
            size: A4;
            margin: 2.5cm 0.75cm 2cm 0.75cm;  /* top right bottom left */
            @top-right {
                content: "Staatskanzlei";
                font-family: Helvetica, Arial, sans-serif;
                font-size: 8pt;
            }
        }

        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 7pt;
            line-height: 1.2;
        }

        .address {
            margin-left: 1.0cm;
            margin-bottom: 0.5cm;
            font-size: 8pt;
            line-height: 1.4;
        }

        .date {
            margin-left: 1.0cm;
            margin-bottom: 2cm;
            font-size: 8pt;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            table-layout: fixed;
            white-space: nowrap;
        }

        /* Column widths for the first row */
        .header-row td {
            background-color: #707070;
            color: white;
            font-weight: bold;
            text-align: left;
            padding: 2pt;
            border: 1pt solid #000;
        }

        th, td {
            padding: 2pt;
            border: 1pt solid #000;
        }
        
        
        /* Fixed column widths for main table */
        .first-table td:first-child { width: 30pt; }
        .first-table td:nth-child(2){ width: 305pt;}
        .first-table td:nth-child(3){ width: 50pt; }
        .first-table td:last-child { width: 50pt; }
        
        /* Fixed column widths for parliamentarian summary table */
        .parliamentarian-summary-table td:first-child { width: 360pt; }
        .parliamentarian-summary-table td:nth-child(2) { width: 50pt; }
        .parliamentarian-summary-table td:last-child { width: 50pt; }
        
        .numeric { text-align: right; }
        
        .first-table tr:nth-child(2) td {
            background-color: #d5d7d9;
        }
            
        .first-table tr:nth-child(even):not(.total-row) td {
            background-color: #f3f3f3;
        }

        .parliamentarian-summary-table {
            page-break-inside: avoid;
            margin-top: 1cm;
        }

        .parliamentarian-summary-table td {
            font-weight: bold;
            background-color: #d5d7d9;
        }
    """)

    data = _get_parliamentarian_settlement_data(
        settlement_run, request, parliamentarian
    )

    html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div class="address">
                Staatskanzlei<br>
                {parliamentarian.shipping_address}<br>
                {parliamentarian.shipping_address_zip_code} {parliamentarian.shipping_address_city}
            </div>

            <div class="date">
                {settlement_run.end.strftime('%d.%m.%Y')}
            </div>

            <table class="first-table">
                <thead>
                    <tr class="header-row">
                        <td>Name</td>
                        <td>Zug</td>
                        <td>ALG</td>
                        <td colspan="2">KR-{settlement_run.start.year}
                        -{(settlement_run.start.month-1)//3 + 1:02d}</td>
                    </tr>
                    <tr>
                        <th class="data-column-date">Datum</th>
                        <th class="data-column-type">Typ</th>
                        <th class="data-column-value">Wert</th>
                        <th class="data-column-chf">CHF ohne Tz</th>
                    </tr>
                </thead>
                <tbody>
    """

    type_totals = {
        'plenary': {'entries': [], 'total': Decimal('0')},
        'commission': {'entries': [], 'total': Decimal('0')},
        'study': {'entries': [], 'total': Decimal('0')},
        'shortest': {'entries': [], 'total': Decimal('0')},
        'expenses': {'entries': [], 'total': Decimal('0')}
    }

    for entry in data['entries']:
        html += f"""
            <tr>
                <td>{entry[0].strftime('%d.%m.%Y')}</td>
                <td>{entry[1]}</td>
                <td class="numeric">{entry[2]}</td>
                <td class="numeric">{entry[4]:,.2f}</td>
            </tr>
        """
        if entry[1] not in ['Total', 'Auszahlung']:
            type_totals[entry[5]]['entries'].append(entry)
            type_totals[entry[5]]['total'] += entry[4]

    html += """
        </tbody>
    </table>
    
    <table class="parliamentarian-summary-table">
        <tbody>
    """

    total = Decimal('0')
    for type_name, type_key in [
        ('Total aller Plenarsitzungen inkl. Teuerungszulage', 'plenary'),
        ('Total aller Kommissionssitzungen inkl. Teuerungszulage',
         'commission'),
        ('Total aller Aktenstudium inkl. Teuerungszulage', 'study'),
        ('Total aller Kürzestsitzungen inkl. Teuerungszulage', 'shortest'),
            ('Total Spesen inkl. Teuerungszulage', 'expenses')
    ]:
        total_value = sum(Decimal(str(e[2])) for e in type_totals[type_key]['entries'])
        total_chf = type_totals[type_key]['total']
        total += total_chf
        html += f"""
            <tr>
                <td>{type_name}</td>
                <td class="numeric">{total_value:,.2f}</td>
                <td class="numeric">{total_chf:,.2f}</td>
            </tr>
        """

    html += f"""
            <tr>
                <td>Total Auszahlung</td>
                <td class="numeric">-</td>
                <td class="numeric">{total:,.2f}</td>
            </tr>
        </tbody>
    </table>
    </body>
    </html>
    """

    # Convert numbers to Swiss format
    html = html.replace(',', "'")
    return HTML(string=html).write_pdf(stylesheets=[css], font_config=font_config)


def _get_parliamentarian_settlement_data(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    parliamentarian: Parliamentarian,
) -> dict[str, list['ParliamentarianEntry']]:
    """Get settlement data for a specific parliamentarian."""
    # todo: Here we'll have to add 'Spense' in the future

    session = request.session
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == settlement_run.start.year)
        .first()
    )

    if not rate_set:
        return {'entries': []}

    attendences = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end
    ).query().filter(
        Attendence.parliamentarian_id == parliamentarian.id
    )

    result = []

    for attendence in attendences:
        is_president = any(r.role == 'president'
                           for r in parliamentarian.roles)

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            )
        )

        # Build type description
        type_desc = request.translate(TYPES[attendence.type])
        if attendence.commission:
            type_desc = f'{type_desc} - {attendence.commission.name}'

        result.append((
            attendence.date,
            type_desc,
            attendence.calculate_value(),
            Decimal('0'),  # Placeholder value to maintain tuple structure
            Decimal(str(base_rate)),  # Base rate without COLA
            attendence.type  # Store type for totals calculation
        ))

    # Sort by date
    result.sort(key=lambda x: x[0])

    return {
        'entries': result
    }


def generate_settlement_pdf(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    entity_type: Literal['all', 'commission', 'party', 'parliamentarian'],
    entity: 'Commission | Party | Parliamentarian | None' = None,
) -> bytes:
    """Generate PDF for settlement data."""
    font_config = FontConfiguration()
    css = CSS(string=PDF_CSS)

    if entity_type == 'commission' and isinstance(entity, Commission):
        settlement_data = _get_commission_settlement_data(
            settlement_run, request, entity
        )
        totals = _get_commission_totals(settlement_run, request, entity)

    elif entity_type == 'party' and isinstance(entity, Party):
        settlement_data = _get_party_settlement_data(
            settlement_run, request, entity
        )
        totals = _get_party_specific_totals(settlement_run, request, entity)

    elif entity_type == 'all':
        settlement_data = _get_settlement_data(settlement_run, request)
        totals = _get_party_totals(settlement_run, request)
    else:
        raise ValueError(f'Unsupported entity type: {entity_type}')

    html = _generate_settlement_html(
        settlement_data=settlement_data,
        totals=totals,
        subtitle='Einträge Journal',
    )

    return HTML(
        string=html.replace(',', "'"),  # Swiss number format
    ).write_pdf(stylesheets=[css], font_config=font_config)


def _get_commission_settlement_data(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    commission: Commission
) -> list[tuple['date', str, str, str | int, Decimal, Decimal]]:
    """Get settlement data for a specific commission."""
    session = request.session
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == settlement_run.start.year)
        .first()
    )

    if not rate_set:
        return []

    attendences = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end
    ).query().filter(
        Attendence.commission_id == commission.id
    )

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    result = []
    for attendence in attendences:
        is_president = any(r.role == 'president'
                           for r in attendence.parliamentarian.roles)

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=commission.type
        )

        rate_with_cola = Decimal(str(base_rate)) * cola_multiplier

        result.append((
            attendence.date,
            f'{attendence.parliamentarian.first_name} '
            f'{attendence.parliamentarian.last_name}',
            request.translate(TYPES[attendence.type]),
            attendence.calculate_value(),
            Decimal(str(base_rate)),
            rate_with_cola
        ))

    return sorted(result, key=lambda x: x[0])


def _generate_settlement_html(
    settlement_data: list[
        tuple['date', str, str, str | int, Decimal, Decimal]
    ],
    totals: list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]],
    subtitle: str,
) -> str:
    """Generate HTML for settlement PDF."""
    html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <table class="journal-table">
                <thead>
                    <tr>
                        <th colspan="6">{subtitle}</th>
                    </tr>
                    <tr>
                        <th>Datum</th>
                        <th>Person</th>
                        <th>Typ</th>
                        <th>Wert</th>
                        <th>CHF</th>
                        <th>CHF + TZ</th>
                    </tr>
                </thead>
                <tbody>
    """

    for row in settlement_data:
        html += f"""
            <tr>
                <td>{row[0].strftime('%d.%m.%Y')}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td class="numeric">{row[3]}</td>
                <td class="numeric">{row[4]:,.2f}</td>
                <td class="numeric">{row[5]:,.2f}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
        <table class="summary-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Sitzungen</th>
                    <th>Spesen</th>
                    <th>Total Einträge</th>
                    <th>Teuerungszulagen</th>
                    <th>Auszahlung</th>
                </tr>
            </thead>
            <tbody>
    """

    for i, row in enumerate(totals):
        is_last = (i == len(totals) - 1)
        is_total = is_last
        row_class = ' class="total-row"' if is_total else ''
        html += f"""
            <tr{row_class}>
                <td>{row[0]}</td>
                <td class="numeric">{row[1]:,.2f}</td>
                <td class="numeric">{row[2]:,.2f}</td>
                <td class="numeric">{row[3]:,.2f}</td>
                <td class="numeric">{row[4]:,.2f}</td>
                <td class="numeric">{row[5]:,.2f}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
        </body>
        </html>
    """

    return html


def _get_settlement_data(
    self: SettlementRun, request: 'TownRequest'
) -> list[Any]:

    session = request.session
    # Get rate set for the year
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == self.start.year)
        .first()
    )

    if not rate_set:
        return []

    # Use collection to get all attendences in period
    attendences = AttendenceCollection(
        session,
        date_from=self.start,
        date_to=self.end
    )

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    settlement_data = []

    # Group by parliamentarian for summary
    parliamentarian_totals: dict[str, Decimal] = {}

    for attendence in attendences.query():
        is_president = any(r.role == 'president'
                           for r in attendence.parliamentarian.roles)

        # Calculate base rate
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            ),
        )

        # Apply cost of living adjustment
        rate_with_cola = Decimal(base_rate * cola_multiplier)

        # Build description of the session/meeting
        translated_type = request.translate(TYPES[attendence.type])

        if attendence.type == 'plenary':
            type_desc = translated_type
        elif attendence.type == 'commission' or attendence.type == 'study':
            commission_name = (
                attendence.commission.name if attendence.commission else ''
            )
            type_desc = f'{translated_type} - {commission_name}'
        else:  # shortest
            type_desc = translated_type

        # Add row for this attendence
        settlement_data.append(
            (
                attendence.date,
                f'{attendence.parliamentarian.first_name} '
                f'{attendence.parliamentarian.last_name}',
                type_desc,
                attendence.calculate_value(),
                base_rate,
                rate_with_cola,
            )
        )

        # Update parliamentarian total
        parliamentarian_id = str(attendence.parliamentarian.id)
        if parliamentarian_id not in parliamentarian_totals:
            parliamentarian_totals[parliamentarian_id] = Decimal('0')
        parliamentarian_totals[parliamentarian_id] += rate_with_cola

    # Sort by date
    settlement_data.sort(key=lambda x: x[0])
    return settlement_data


def _get_commission_totals(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    commission: Commission
) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]]:
    """Get totals for a specific commission grouped by party."""
    session = request.session

    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == settlement_run.start.year)
        .first()
    )

    if not rate_set:
        return []

    # Get all attendences in period for this commission
    attendences = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end,
        commission_id=str(commission.id)
    ).query()

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Initialize party totals
    party_totals: dict[str, dict[str, Decimal]] = {}

    for attendence in attendences:
        # Get parliamentarian's party
        current_party = None
        for role in attendence.parliamentarian.roles:
            if role.party and (role.end is None
                               or role.end >= settlement_run.start):
                current_party = role.party
                break

        if not current_party:
            continue

        party_name = current_party.name

        if party_name not in party_totals:
            party_totals[party_name] = {
                'Meetings': Decimal('0'),
                'Expenses': Decimal('0'),
                'Total': Decimal('0'),
                'Cost-of-living Allowance': Decimal('0'),
                'Final': Decimal('0')
            }

        is_president = any(r.role == 'president'
                         for r in attendence.parliamentarian.roles)

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=commission.type
        )

        # Update totals
        party_totals[party_name]['Meetings'] += Decimal(str(base_rate))
        base_total = party_totals[party_name]['Meetings']
        cola_amount = base_total * (cola_multiplier - 1)

        expenses = party_totals[party_name]['Expenses'] + base_total
        party_totals[party_name]['Total'] = base_total + expenses
        party_totals[party_name]['Cost-of-living Allowance'] = cola_amount
        party_totals[party_name]['Final'] = base_total + cola_amount

    # Convert to sorted list of tuples
    result = [
        (
            name,
            data['Meetings'],
            data['Expenses'],
            data['Total'],
            data['Cost-of-living Allowance'],
            data['Final']
        )
        for name, data in sorted(party_totals.items())
    ]

    # Add total row
    totals = (
        sum(r[1] for r in result),  # Sessions
        sum(r[2] for r in result),  # Expenses
        sum(r[3] for r in result),  # Total
        sum(r[4] for r in result),  # COLA
        sum(r[5] for r in result),  # Final
    )

    result.append((
        f'Total {commission.name}',
        Decimal(str(totals[0])),
        Decimal(str(totals[1])),
        Decimal(str(totals[2])),
        Decimal(str(totals[3])),
        Decimal(str(totals[4]))
    ))

    return result


def _get_party_settlement_data(
    settlement_run: SettlementRun,
    request: 'TownRequest',
    party: Party
) -> list[tuple['date', str, str, str | int, Decimal, Decimal]]:
    """Get settlement data for a specific party."""
    session = request.session
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == settlement_run.start.year)
        .first()
    )

    if not rate_set:
        return []

    # Get all attendences in period
    attendences = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end
    ).query()

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    result = []
    for attendence in attendences:
        # Check if parliamentarian belongs to this party
        current_party = None
        for role in attendence.parliamentarian.roles:
            if role.party and (
                    role.end is None or role.end >= settlement_run.start):
                current_party = role.party
                break

        if not current_party or current_party.id != party.id:
            continue

        is_president = any(r.role == 'president'
                           for r in attendence.parliamentarian.roles)

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            )
        )

        rate_with_cola = Decimal(str(base_rate)) * cola_multiplier

        type_desc = request.translate(TYPES[attendence.type])
        if attendence.commission:
            type_desc = f'{type_desc} - {attendence.commission.name}'

        result.append((
            attendence.date,
            f'{attendence.parliamentarian.first_name}'
            f' {attendence.parliamentarian.last_name}',
            type_desc,
            attendence.calculate_value(),
            Decimal(str(base_rate)),
            rate_with_cola
        ))

    return sorted(result, key=lambda x: x[0])


def _get_party_specific_totals(
    settlement_run: SettlementRun, request: 'TownRequest', party: Party
) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]]:
    """Get totals for a specific party."""
    session = request.session
    rate_set = (
        session.query(RateSet)
        .filter(RateSet.year == settlement_run.start.year)
        .first()
    )

    if not rate_set:
        return []

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Initialize parliamentarian totals for this party
    parliamentarian_totals: dict[str, dict[str, Decimal]] = {}

    attendences = AttendenceCollection(
        session, date_from=settlement_run.start, date_to=settlement_run.end
    ).query()

    for attendence in attendences:
        # Check if parliamentarian belongs to this party
        current_party = None
        for role in attendence.parliamentarian.roles:
            if role.party and (
                role.end is None or role.end >= settlement_run.start
            ):
                current_party = role.party
                break

        if not current_party or current_party.id != party.id:
            continue

        name = (f'{attendence.parliamentarian.first_name}'
                f' {attendence.parliamentarian.last_name}')

        if name not in parliamentarian_totals:
            parliamentarian_totals[name] = {
                'Meetings': Decimal('0'),
                'Expenses': Decimal('0'),
                'Total': Decimal('0'),
                'Cost-of-living Allowance': Decimal('0'),
                'Final': Decimal('0'),
            }

        is_president = any(
            r.role == 'president' for r in attendence.parliamentarian.roles
        )

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type
                if attendence.commission
                else None
            ),
        )

        parliamentarian_totals[name]['Meetings'] += Decimal(str(base_rate))
        base_total = parliamentarian_totals[name]['Meetings']
        cola_amount = base_total * (cola_multiplier - 1)

        parliamentarian_totals[name]['Total'] = base_total
        parliamentarian_totals[name][
            'Cost-of-living Allowance'
        ] = cola_amount
        parliamentarian_totals[name]['Final'] = base_total + cola_amount

    # Convert to sorted list of tuples
    result = [
        (
            name,
            data['Meetings'],
            data['Expenses'],
            data['Total'],
            data['Cost-of-living Allowance'],
            data['Final'],
        )
        for name, data in sorted(parliamentarian_totals.items())
    ]

    # Add party total row
    totals = (
        sum(r[1] for r in result),  # Meetings
        sum(r[2] for r in result),  # Expenses
        sum(r[3] for r in result),  # Total
        sum(r[4] for r in result),  # COLA
        sum(r[5] for r in result),  # Final
    )

    result.append(
        (
            f'Total {party.name}',
            Decimal(str(totals[0])),
            Decimal(str(totals[1])),
            Decimal(str(totals[2])),
            Decimal(str(totals[3])),
            Decimal(str(totals[4])),
        )
    )

    return result


@PasApp.view(
    model=SettlementRunAllExport,
    permission=Private,
    name='run-export',
    request_method='GET'
)
def view_settlement_run_all_export(
    self: SettlementRunAllExport,
    request: 'TownRequest'
) -> Response:
    """Generate export data for a specific entity in a settlement run."""

    if self.category == 'all-parties':
        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='all',
            title='Einträge Journal Gesamtabrechnung'
        )
        filename = request.translate(_('Total all parties'))
        return Response(
            pdf_bytes,
            content_type='application/pdf',
            content_disposition=f'attachment; filename={filename}.pdf'
        )
    else:
        raise NotImplementedError()


@PasApp.view(
    model=SettlementRunExport,
    permission=Private,
    name='run-export',
    request_method='GET'
)
def view_settlement_run_export(
    self: SettlementRunExport,
    request: 'TownRequest'
) -> Response:
    """Generate export data for a specific entity in a settlement run."""
    if self.category == 'party':
        if not isinstance(self.entity, Party):
            raise TypeError('Entity must be a Party for party settlements')

        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='party',
            entity=self.entity,
        )
        filename = f'party_{self.entity.name}'

    elif self.category == 'commission':
        if not isinstance(self.entity, Commission):
            raise TypeError(
                'Entity must be a Commission for commission settlements'
            )

        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='commission',
            entity=self.entity,
        )
        filename = f'commission_{self.entity.name}'

    elif self.category == 'parliamentarian':
        if not isinstance(self.entity, Parliamentarian):
            raise TypeError('Entity must be a Parliamentarian')
        pdf_bytes = generate_parliamentarian_settlement_pdf(
            self.settlement_run, request, self.entity
        )
        filename = (
            f'parliamentarian_{self.entity.last_name}_{self.entity.first_name}'
        )
        return Response(
            pdf_bytes,
            content_type='application/pdf',
            content_disposition=f'attachment; filename={filename}.pdf'
        )

    else:
        raise NotImplementedError(
            f'Export category {self.category} not implemented'
        )

    return Response(
        pdf_bytes,
        content_type='application/pdf',
        content_disposition=f'attachment; filename={filename}.pdf'
    )


@PasApp.form(
    model=SettlementRun,
    name='edit',
    template='form.pt',
    permission=Private,
    form=SettlementRunForm
)
def edit_settlement_run(
    self: SettlementRun,
    request: 'TownRequest',
    form: SettlementRunForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = SettlementRunLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=SettlementRun,
    request_method='DELETE',
    permission=Private
)
def delete_settlement_run(
    self: SettlementRun,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = SettlementRunCollection(request.session)
    collection.delete(self)

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import SettlementRunCollection,\
    AttendenceCollection
from onegov.pas.forms import SettlementRunForm
from onegov.pas.layouts import SettlementRunCollectionLayout
from onegov.pas.layouts import SettlementRunLayout
from onegov.pas.models import (
    SettlementRun,
    Party,
    RateSet,
)
from webob import Response
from sqlalchemy import or_
from decimal import Decimal
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration)
from onegov.pas.models.attendence import TYPES
from onegov.pas.path import SettlementRunExport, SettlementRunAllExport


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


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
    # commissions = request.session.query(Commission).filter(
    #     or_(
    #         Commission.end.is_(None),
    #         Commission.end >= self.start
    #     ),
    #     Commission.start <= self.end
    # ).order_by(Commission.name)
    #
    # # Get parliamentarians active during settlement run period
    # parliamentarians = [
    #     p
    #     for p in request.session.query(Parliamentarian).order_by(
    #         Parliamentarian.last_name, Parliamentarian.first_name
    #     )
    #     if p.active_during(self.start, self.end)
    # ]

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
                           category='settlements-by-party'
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
                        SettlementRunAllExport(  # Use new model
                            settlement_run=self,
                            category='all-parties'
                        ),
                        name='run-export'
                    ),
                )
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


def generate_pdf_all_settlements(
    self: SettlementRun,
    request: 'TownRequest'
) -> bytes:
    """Generate PDF with all parties."""
    font_config = FontConfiguration()
    css = CSS(
        string="""
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
    table-layout: auto;
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
    )

    settlement_data = _get_settlement_data(self, request)
    party_totals = _get_party_totals(self, request)

    html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            <table class="journal-table">
                <thead>
                    <tr>
                        <th colspan="6">Einträge Journal</th>
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
        is_total = row[1].startswith('Total')
        row_class = ' class="total-row"' if is_total else ''

        html += f"""
            <tr{row_class}>
                <td>{row[0].strftime('%d.%m.%Y')}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td class="numeric">{row[3]}</td>
                <td class="numeric">{row[4]:,.2f}</td>
                <td class="numeric">{row[5]:,.2f}</td>
            </tr>
        """

    # Add summary table
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

    for row in party_totals:
        is_total = row[0] == 'Total Parteien'
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

    return HTML(
        string=html.replace(',', "'"),  # Swiss number format
    ).write_pdf(stylesheets=[css], font_config=font_config)


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
        pdf_bytes = generate_pdf_all_settlements(
            self.settlement_run, request
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
    # Here generate the export data based on:
    # - self.settlement_run (the run being exported)
    # - self.entity (the specific party/commission/parliamentarian)
    # - self.category (A granular description of the type of export)

    # Example CSV data
    csv_data = """Date,Hours,Amount
    2024-01-01,2.5,250
    2024-01-02,3.0,300
    2024-01-03,1.5,150"""
    return Response(
        csv_data,
        content_type='text/csv',
        content_disposition=f'attachment; filename=export_{self.entity.id}.csv'
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

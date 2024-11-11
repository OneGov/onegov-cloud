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
    Parliamentarian, RateSet,
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

th:nth-child(1), /* Datum */
td:nth-child(1) {
    width: 40pt;
}
/* Add width control for specific columns */
th:nth-child(4), /* Wert  */
td:nth-child(4) {
    width: 40pt;
}
th:nth-child(5), /* CHF column */
td:nth-child(5) {
    width: 40pt;
}

th:nth-child(6), /* CHF + TZ column */
td:nth-child(6) {
    width: 40pt;
}

th:nth-child(6), /* Person */
td:nth-child(6) {
    width: 120pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1cm;
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

/* Column headers */
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

/* Alternating row colors */
tr:nth-child(even):not(.total-row) td {
    background-color: #f2f2f2;
}

.numeric {
    text-align: right;
}

h1 {
    font-size: 14pt;
    margin-bottom: 0.5cm;
}

.subtitle {
    font-size: 11pt;
    color: #666;
    margin-bottom: 1cm;
}

.total-row {
    font-weight: bold;
    background-color: #f2f2f2;
}
    """
    )

    settlement_data = _get_settlement_data(self, request)
    html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>

            <table>
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
        elif attendence.type == 'commission':
            commission_name = (
                attendence.commission.name if attendence.commission else ''
            )
            type_desc = f'{translated_type} - {commission_name}'
        elif attendence.type == 'study':
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

    # Add summary rows at end
    settlement_data.append(
        (
            self.end,  # Use end date for summary rows
            'TOTAL',
            '',
            '',
            Decimal(str(sum(row[4] for row in settlement_data[:-1]))),
            Decimal(str(sum(row[5] for row in settlement_data[:-1]))),
        )
    )

    # Add per-parliamentarian totals
    for parliamentarian_id, total in parliamentarian_totals.items():
        parliamentarian = session.query(Parliamentarian).get(
            parliamentarian_id
        )
        if parliamentarian:
            settlement_data.append(
                (
                    self.end,
                    f'Total {parliamentarian.first_name}'
                    f' {parliamentarian.last_name}',
                    '',
                    '',
                    total / cola_multiplier,  # Base amount
                    total,  # With COLA
                )
            )

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

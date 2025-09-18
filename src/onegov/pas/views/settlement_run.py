from __future__ import annotations

from io import BytesIO
from webob import Response
from onegov.core.utils import module_path
from decimal import Decimal
from operator import itemgetter
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration)

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.utils import normalize_for_filename
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
    SettlementRunCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.export_single_parliamentarian import (
    generate_parliamentarian_settlement_pdf
)
from onegov.pas.forms import SettlementRunForm
from onegov.pas.layouts import SettlementRunCollectionLayout
from onegov.pas.layouts import SettlementRunLayout
from onegov.pas.models import (
    Attendence,
    PASCommission,
    PASCommissionMembership,
    PASParliamentarian,
    Party,
    SettlementRun,
)
from onegov.pas.models.attendence import TYPES
from onegov.pas.path import SettlementRunExport, SettlementRunAllExport
from onegov.pas.utils import (
    format_swiss_number,
    get_commissions_with_memberships,
    get_parliamentarians_with_settlements,
    get_parties_with_settlements,
    is_commission_president,
)
from onegov.pas.views.abschlussliste import (
    generate_abschlussliste_xlsx,
    generate_buchungen_abrechnungslauf_xlsx
)
from onegov.pas.views.pas_excel_export_nr_3_lohnart_fibu import (
        generate_fibu_export_rows)


from typing import Any, Literal, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from datetime import date
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest

    SettlementDataRow: TypeAlias = tuple[
        'date', PASParliamentarian, str, Decimal, Decimal, Decimal
    ]
    TotalRow: TypeAlias = tuple[
        str, Decimal, Decimal, Decimal, Decimal, Decimal
    ]


XLSX_MIMETYPE = (
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


def get_commission_closure_status(
    session: Session,
    settlement_run: SettlementRun,
    commissions: list[PASCommission] | None = None
) -> list[dict[str, Any]]:
    """
    Get closure status organized by commission showing completion summary.

    Args:
        session: Database session
        settlement_run: The settlement run to check
        commissions: Optional pre-fetched list of commissions

    Returns:
        List of dicts with structure:
        [
            {
                'commission_name': str,
                'total_members': int,
                'completed_members': int,
                'completion_ratio': str,
                'incomplete_members': [
                    {'name': str, 'has_attendance': bool}, ...
                ]
            }, ...
        ]
    """
    # Query commissions if not provided
    if commissions is None:
        commissions = get_commissions_with_memberships(
            session, settlement_run.start, settlement_run.end
        )

    commission_status = []

    for commission in commissions:
        # Get all members of this commission during settlement period
        memberships = session.query(PASCommissionMembership).filter(
            PASCommissionMembership.commission_id == commission.id,
            (
                PASCommissionMembership.start.is_(None)
                | (PASCommissionMembership.start <= settlement_run.end)
            ),
            (
                PASCommissionMembership.end.is_(None)
                | (PASCommissionMembership.end >= settlement_run.start)
            )
        ).all()

        total_members = len(memberships)
        if total_members == 0:
            continue

        completed_members = 0
        incomplete_members = []
        complete_members = []

        for membership in memberships:
            parliamentarian = membership.parliamentarian
            parl_name = (
                f'{parliamentarian.first_name} '
                f'{parliamentarian.last_name}'
            )

            # Check if this parliamentarian has closed attendance for this
            # commission
            closed_attendance = session.query(Attendence).filter(
                Attendence.parliamentarian_id == parliamentarian.id,
                Attendence.commission_id == commission.id,
                Attendence.date >= settlement_run.start,
                Attendence.date <= settlement_run.end,
                Attendence.abschluss == True
            ).first()

            if closed_attendance:
                completed_members += 1
                complete_members.append({
                    'name': parl_name,
                })
            else:
                # Check if they have any attendance at all for this commission
                has_attendance = session.query(Attendence).filter(
                    Attendence.parliamentarian_id == parliamentarian.id,
                    Attendence.commission_id == commission.id,
                    Attendence.date >= settlement_run.start,
                    Attendence.date <= settlement_run.end
                ).first() is not None

                incomplete_members.append({
                    'name': parl_name,
                    'has_attendance': has_attendance
                })

        completion_ratio = f'{completed_members}/{total_members}'

        commission_status.append({
            'commission_name': commission.name,
            'total_members': total_members,
            'completed_members': completed_members,
            'completion_ratio': completion_ratio,
            'complete_members': complete_members,
            'incomplete_members': incomplete_members,
            'is_complete': completed_members == total_members
        })

    # Sort by completion status (incomplete first) then by name
    commission_status.sort(
        key=itemgetter('is_complete', 'commission_name')
    )

    return commission_status


@PasApp.html(
    model=SettlementRunCollection,
    template='settlement_runs.pt',
    permission=Private
)
def view_settlement_runs(
    self: SettlementRunCollection,
    request: TownRequest
) -> RenderData:

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


@PasApp.form(model=SettlementRunCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=SettlementRunForm
)
def add_settlement_run(
    self: SettlementRunCollection,
    request: TownRequest,
    form: SettlementRunForm
) -> RenderData | Response:

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
    request: TownRequest
) -> RenderData:
    """ A page where all exports are listed and grouped by category. """
    layout = SettlementRunLayout(self, request)
    session = request.session

    # Get parties active during settlement run period
    parties = get_parties_with_settlements(session, self.start, self.end)

    # Get commissions active during settlement run period
    commissions = get_commissions_with_memberships(
        session, self.start, self.end
    )

    # Get parliamentarians active during settlement run period with settlements
    parliamentarians = get_parliamentarians_with_settlements(
        session, self.start, self.end
    )

    # Get commission closure status for the control list
    commission_closure_status = get_commission_closure_status(
        session, self, commissions
    )

    pdf_categories = {
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
            'title': _('All Settlements'),
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
                ),
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

    excel_categories = {
        'abschlussliste_export': {
            'title': _('Abschlussliste'),
            'links': [
                Link(
                    _('Abschlussliste (XLSX)'),
                    request.link(
                        SettlementRunAllExport(
                            settlement_run=self,
                            category='abschlussliste-xlsx-export'
                        ),
                        name='run-export'
                    ),
                )
            ]
        },
        'salary_export': {
            'title': _('Buchungen Abrechnungslauf'),
            'links': [
                Link(
                    _('Buchungen Abrechnungslauf (Kontrollliste)'),
                    request.link(
                        SettlementRunAllExport(
                            settlement_run=self,
                            category='buchungen-abrechnungslauf-kontroll-xlsx-export'
                        ),
                        name='run-export'
                    ),
                ),
            ]
        },
        'fibu_export': {
            'title': _('KR-Entschädigungen (CSV)'),
            'links': [
                Link(
                    _('KR-Entschädigungen (CSV)'),
                    request.link(
                        SettlementRunAllExport(
                            settlement_run=self,
                            category='fibu-csv-export'
                        ),
                        name='run-export'
                    ),
                )
            ]
        }
    }

    export_tabs_data = {
        'pdf': {
            'tab_title': _('PDF Exports'),
            'panel_id': 'panel-pdf-exports',
            'categories': pdf_categories
        },
        'excel': {
            'tab_title': _('Excel Exports'),
            'panel_id': 'panel-excel-exports',
            'categories': excel_categories
        }
    }

    return {
        'layout': layout,
        'settlement_run': self,
        'export_tabs_data': export_tabs_data,
        'commission_closure_status': commission_closure_status,
        'title': layout.title,
    }


def _get_commission_totals(
    settlement_run: SettlementRun,
    request: TownRequest,
    commission: PASCommission
) -> list[TotalRow]:
    """Get totals for a specific commission grouped by party."""
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)

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

        is_president = is_commission_president(
            attendence.parliamentarian, commission.id, settlement_run
        )

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=commission.type
        )

        # Update totals
        party_totals[party_name]['Meetings'] += Decimal(str(base_rate))

        # Note: Expenses will be implemented in the future
        base_total = party_totals[party_name]['Meetings']
        expenses = party_totals[party_name]['Expenses']
        cola_amount = base_total * (cola_multiplier - 1)

        party_totals[party_name]['Total'] = base_total + expenses
        party_totals[party_name]['Cost-of-living Allowance'] = cola_amount
        party_totals[party_name]['Final'] = base_total + expenses + cola_amount

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


def _get_party_totals_for_export_all(
    self: SettlementRun, request: TownRequest
) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]]:
    """Get totals grouped by party."""
    session = request.session
    rate_set = get_current_rate_set(session, self)
    if not rate_set:
        return []

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Get all parties with settlements during the period
    parties = get_parties_with_settlements(session, self.start, self.end)

    # Initialize party totals
    party_totals: dict[str, dict[str, Decimal]] = {
        party.name: {
            'Meetings': Decimal('0'),
            'Expenses': Decimal('0'),
            'Total': Decimal('0'),
            'Cost-of-living Allowance': Decimal('0'),
            'Final': Decimal('0'),
        }
        for party in parties
    }

    # Process attendances for each party with proper temporal alignment
    for party in parties:
        attendances = (
            AttendenceCollection(session)
            .by_party(
                party_id=str(party.id),
                start_date=self.start,
                end_date=self.end,
            )
            .query()
            .all()
        )

        for attendance in attendances:
            # Calculate base rate
            is_president = any(
                r.role == 'president'
                for r in attendance.parliamentarian.roles
            )

            base_rate = calculate_rate(
                rate_set=rate_set,
                attendence_type=attendance.type,
                duration_minutes=int(attendance.duration),
                is_president=is_president,
                commission_type=(
                    attendance.commission.type
                    if attendance.commission
                    else None
                ),
            )

            # Update totals
            party_totals[party.name]['Meetings'] += Decimal(str(base_rate))
            base_total = party_totals[party.name]['Meetings']
            expenses = party_totals[party.name]['Expenses']
            cola_amount = base_total * (cola_multiplier - 1)

            party_totals[party.name]['Total'] = base_total + expenses
            party_totals[party.name]['Cost-of-living Allowance'] = cola_amount
            party_totals[party.name]['Final'] = (
                    base_total + expenses + cola_amount
            )

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


def generate_settlement_pdf(
    settlement_run: SettlementRun,
    request: TownRequest,
    entity_type: Literal['all', 'commission', 'party', 'parliamentarian'],
    entity: PASCommission | Party | PASParliamentarian | None = None,
) -> bytes:
    """ Entry point for almost all settlement PDF generations. """
    font_config = FontConfiguration()
    css_path = module_path('onegov.pas', 'views/templates/settlement_pdf.css')
    with open(css_path) as f:
        css = CSS(string=f.read())

    if entity_type == 'commission' and isinstance(entity, PASCommission):
        settlement_data = _get_commission_settlement_data(
            settlement_run, request, entity
        )
        totals = _get_commission_totals(settlement_run, request, entity)

    elif entity_type == 'party' and isinstance(entity, Party):
        settlement_data = _get_party_settlement_data(
            settlement_run, request, entity
        )
        totals = get_party_specific_totals(settlement_run, request, entity)

    elif entity_type == 'all':
        settlement_data = _get_data_export_all(settlement_run, request)
        totals = _get_party_totals_for_export_all(settlement_run, request)
        assert len(totals) > 0
    else:
        raise ValueError(f'Unsupported entity type: {entity_type}')

    html = _generate_settlement_html(
        settlement_data=settlement_data,
        totals=totals,
        subtitle='Einträge Journal',
    )

    return HTML(string=html).write_pdf(
        stylesheets=[css], font_config=font_config
    )


def _get_commission_settlement_data(
    settlement_run: SettlementRun,
    request: TownRequest,
    commission: PASCommission
) -> list[SettlementDataRow]:
    """Get settlement data for a specific commission."""
    session = request.session
    rate_set = get_current_rate_set(request.session, settlement_run)

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
        is_president = is_commission_president(
            attendence.parliamentarian, commission.id, settlement_run
        )

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
            attendence.parliamentarian,
            request.translate(TYPES[attendence.type]),
            attendence.calculate_value(),
            Decimal(str(base_rate)),
            rate_with_cola
        ))

    return sorted(result, key=itemgetter(0))


def _generate_settlement_html(
    settlement_data: list[SettlementDataRow],
    totals: list[TotalRow],
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
                       <th colspan="7">{subtitle}</th>
                   </tr>
                   <tr>
                       <th>Datum</th>
                       <th>Pers-Nr</th>
                       <th>Person</th>
                       <th>Typ</th>
                       <th>Wert</th>
                       <th>CHF</th>
                       <th>CHF + TZ</th>
                   </tr>
               </thead>
               <tbody>
   """

    for settlement_row in settlement_data:
        name = f'{settlement_row[1].first_name} {settlement_row[1].last_name}'
        html += f"""
           <tr>
               <td>{settlement_row[0].strftime('%d.%m.%Y')}</td>
               <td>{settlement_row[1].personnel_number}</td>
               <td>{name}</td>
               <td>{settlement_row[2]}</td>
               <td class="numeric">{settlement_row[3]}</td>
               <td class="numeric">{settlement_row[4]:,.2f}</td>
               <td class="numeric">{settlement_row[5]:,.2f}</td>
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

    for total_row in totals[:-1]:  # All but last
        html += f"""
           <tr>
               <td>{total_row[0]}</td>
               <td class="numeric">{format_swiss_number(total_row[1])}</td>
               <td class="numeric">{format_swiss_number(total_row[2])}</td>
               <td class="numeric">{format_swiss_number(total_row[3])}</td>
               <td class="numeric">{format_swiss_number(total_row[4])}</td>
               <td class="numeric">{format_swiss_number(total_row[5])}</td>
           </tr>
       """

    # Handle last row separately with total-row class
    if totals:
        final_row = totals[-1]
        html += f"""
           <tr class="total-row">
               <td>{final_row[0]}</td>
               <td class="numeric">{format_swiss_number(final_row[1])}</td>
               <td class="numeric">{format_swiss_number(final_row[2])}</td>
               <td class="numeric">{format_swiss_number(final_row[3])}</td>
               <td class="numeric">{format_swiss_number(final_row[4])}</td>
               <td class="numeric">{format_swiss_number(final_row[5])}</td>
           </tr>
       """

    html += """
           </tbody>
       </table>
       </body>
       </html>
   """

    return html


def _get_data_export_all(
    self: SettlementRun, request: TownRequest
) -> list[SettlementDataRow]:

    session = request.session
    rate_set = get_current_rate_set(session, self)

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

    settlement_data: list[SettlementDataRow] = []  # Add type hint here

    # Group by parliamentarian for summary
    parliamentarian_totals: dict[str, Decimal] = {}

    for attendence in attendences.query():
        is_president = is_commission_president(
            attendence.parliamentarian, attendence, self
        )

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
                attendence.parliamentarian,
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
    settlement_data.sort(key=itemgetter(0))
    return settlement_data


def get_party_specific_totals(
    settlement_run: SettlementRun, request: TownRequest, party: Party
) -> list[TotalRow]:
    """Get totals for a specific party."""
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Use AttendenceCollection with party filter
    attendences = (
        AttendenceCollection(
            session,
            date_from=settlement_run.start,
            date_to=settlement_run.end,
            party_id=str(party.id),
        )
        .query()
        .all()
    )

    parliamentarian_totals: dict[str, dict[str, Decimal]] = {}

    for attendence in attendences:
        parliamentarian = attendence.parliamentarian
        name = f'{parliamentarian.first_name} {parliamentarian.last_name}'

        if name not in parliamentarian_totals:
            parliamentarian_totals[name] = {
                'Meetings': Decimal('0'),
                'Expenses': Decimal('0'),
                'Total': Decimal('0'),
                'Cost-of-living Allowance': Decimal('0'),
                'Final': Decimal('0'),
            }

        is_president = any(
            r.role == 'president' for r in parliamentarian.roles
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
        expenses = parliamentarian_totals[name]['Expenses']
        cola_amount = base_total * (cola_multiplier - 1)

        parliamentarian_totals[name]['Total'] = base_total + expenses
        parliamentarian_totals[name]['Cost-of-living Allowance'] = cola_amount
        parliamentarian_totals[name]['Final'] = (
                base_total + expenses + cola_amount
        )

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

    if result:
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


def _get_party_settlement_data(
    settlement_run: SettlementRun,
    request: TownRequest,
    party: Party
) -> list[SettlementDataRow]:
    """Get settlement data for a specific party."""

    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)

    # Get all attendences in period
    attendences = (
        AttendenceCollection(session)
        .by_party(
            party_id=str(party.id),
            start_date=settlement_run.start,
            end_date=settlement_run.end
        )
        .query()
        .all()
    )

    result = []
    for attendence in attendences:

        # Fixme: this check is likely redundant
        current_party = attendence.parliamentarian.get_party_during_period(
            settlement_run.start,
            settlement_run.end,
            session
        )
        if not current_party or current_party.id != party.id:
            continue

        # found an export
        is_president = is_commission_president(
            attendence.parliamentarian, attendence, settlement_run
        )

        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            )
        )

        cola_multiplier = Decimal(
            str(1 + (rate_set.cost_of_living_adjustment / 100))
        )
        rate_with_cola = Decimal(str(base_rate)) * cola_multiplier

        type_desc = request.translate(TYPES[attendence.type])
        if attendence.commission:
            type_desc = f'{type_desc} - {attendence.commission.name}'

        result.append((
            attendence.date,
            attendence.parliamentarian,
            type_desc,
            attendence.calculate_value(),
            Decimal(str(base_rate)),
            rate_with_cola
        ))

    return sorted(result, key=itemgetter(0))


@PasApp.view(
    model=SettlementRunAllExport,
    permission=Private,
    name='run-export',
    request_method='GET'
)
def view_settlement_run_all_export(
    self: SettlementRunAllExport,
    request: TownRequest
) -> Response:
    """Generate export data for a specific entity in a settlement run."""

    if self.category == 'all-parties':
        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='all',
        )
        filename = normalize_for_filename(
            request.translate(_('Total all parties')))
        return Response(
            pdf_bytes,
            content_type='application/pdf',
            content_disposition=f'attachment; filename={filename}.pdf'
        )
    elif self.category == 'abschlussliste-xlsx-export':
        filename = 'Abschlussliste.xlsx'
        output = generate_abschlussliste_xlsx(self.settlement_run, request)
        return Response(
            output.read(),
            content_type=XLSX_MIMETYPE,
            content_disposition=f'attachment; filename="{filename}"'
        )
    elif self.category == 'buchungen-abrechnungslauf-kontroll-xlsx-export':
        filename = 'Buchungen_Abrechnungslauf.xlsx'
        output = generate_buchungen_abrechnungslauf_xlsx(
            self.settlement_run, request)
        return Response(
            output.read(),
            content_type=XLSX_MIMETYPE,
            content_disposition=f'attachment; filename="{filename}"'
        )
    elif self.category == 'fibu-csv-export':
        year = self.settlement_run.end.year
        filename = f'KR-Entschaedigung - {year}.csv'

        output = BytesIO()
        # Use utf-8-sig to ensure proper Excel compatibility with BOM
        csv_data = list(generate_fibu_export_rows(
            self.settlement_run, request))

        # Create CSV content as string
        csv_string = ''
        for row in csv_data:
            # Convert all values to strings and escape quotes
            row_strings = []
            for value in row:
                if value is None:
                    row_strings.append('')  # type: ignore[unreachable]
                else:
                    # Convert to string and handle quotes
                    str_value = str(value)
                    if '"' in str_value:
                        str_value = str_value.replace('"', '""')
                    if (',' in str_value or '"' in str_value or
                            '\n' in str_value):
                        str_value = f'"{str_value}"'
                    row_strings.append(str_value)
            csv_string += ','.join(row_strings) + '\n'

        # Encode to bytes with BOM for Excel compatibility
        csv_bytes = '\ufeff'.encode('utf-8') + csv_string.encode('utf-8')

        return Response(
            csv_bytes,
            content_type='text/csv; charset=utf-8',
            content_disposition=f'attachment; filename="{filename}"'
        )
    else:
        raise NotImplementedError(
            f'Export category {self.category} not implemented for all exports'
        )


@PasApp.view(
    model=SettlementRunExport,
    permission=Private,
    name='run-export',
    request_method='GET'
)
def view_settlement_run_export(
    self: SettlementRunExport,
    request: TownRequest
) -> Response:
    """Generate export data for a specific entity (commission, party or
    parliamentarian) in a settlement run."""

    if self.category == 'party':
        assert isinstance(self.entity, Party)

        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='party',
            entity=self.entity,
        )
        filename = normalize_for_filename(f'Partei_{self.entity.name}')

    elif self.category == 'commission':
        assert isinstance(self.entity, PASCommission)

        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='commission',
            entity=self.entity,
        )
        filename = normalize_for_filename(f'commission_{self.entity.name}')

    elif self.category == 'parliamentarian':
        assert isinstance(self.entity, PASParliamentarian)
        # PASParliamentarian specific export has it's own rendering function
        pdf_bytes = generate_parliamentarian_settlement_pdf(
            self.settlement_run, request, self.entity
        )
        filename = normalize_for_filename(
            f'Parlamentarier_{self.entity.last_name}_{self.entity.first_name}'
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
    request: TownRequest,
    form: SettlementRunForm
) -> RenderData | Response:

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
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = SettlementRunCollection(request.session)
    collection.delete(self)

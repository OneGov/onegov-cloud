from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
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
from onegov.pas.calculate_pay import Compensation
from onegov.pas.calculate_pay import calculate_attendance_compensation
from onegov.pas.calculate_pay import calculate_compensation
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
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.models.presidential_allowance import (
    LOHNART_ALLOWANCE_TEXT,
)


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from datetime import date
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest

    type SettlementDataRow = tuple[
        date, PASParliamentarian, str, Decimal, Decimal, Decimal
    ]
    type TotalRow = tuple[
        str, Decimal, Decimal, Decimal, Decimal, Decimal
    ]


XLSX_MIMETYPE = (
'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)


def _settlement_totals(
    settlement_data: list[SettlementDataRow],
    group_by: Literal['party', 'person'],
    total_label: str,
    session: Session,
    start: date,
    end: date,
) -> list[TotalRow]:
    meeting_compensations: dict[str, Compensation] = {}
    total_compensations: dict[str, Compensation] = {}
    for row in settlement_data:
        parliamentarian = row[1]
        if group_by == 'party':
            party = parliamentarian.get_party_during_period(
                start,
                end,
                session,
            )
            if party is None:
                continue
            name = party.name
        else:
            name = f'{parliamentarian.first_name} {parliamentarian.last_name}'

        compensation = Compensation(base=row[4], adjusted=row[5])
        total_compensations[name] = (
            total_compensations.get(name, Compensation.zero()) + compensation
        )
        if row[2] != LOHNART_ALLOWANCE_TEXT:
            meeting_compensations[name] = (
                meeting_compensations.get(name, Compensation.zero())
                + compensation
            )

    rows: list[TotalRow] = []
    total_meetings = Compensation.zero()
    total_entries = Compensation.zero()
    for name, compensation in sorted(total_compensations.items()):
        meetings = meeting_compensations.get(name, Compensation.zero())
        rows.append(
            (
                name,
                meetings.base,
                Decimal('0'),
                compensation.base,
                compensation.adjustment,
                compensation.adjusted,
            )
        )
        total_meetings += meetings
        total_entries += compensation

    if rows:
        rows.append(
            (
                total_label,
                total_meetings.base,
                Decimal('0'),
                total_entries.base,
                total_entries.adjustment,
                total_entries.adjusted,
            )
        )
    return rows


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

    parliamentarians = get_parliamentarians_with_settlements(
        session, self.start, self.end, settlement_run_id=self.id
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
                    _('All Parliamentarians (ZIP)'),
                    request.link(
                        SettlementRunAllExport(
                            settlement_run=self,
                            category=('all-parliamentarians-zip'),
                        ),
                        name='run-export',
                    ),
                ),
            ]
            + [
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


def generate_settlement_pdf(
    settlement_run: SettlementRun,
    request: TownRequest,
    entity_type: Literal['all', 'commission', 'party', 'parliamentarian'],
    entity: PASCommission | Party | PASParliamentarian | None = None,
) -> bytes:
    """ Entry point for almost all settlement PDF generations excluding
    parliamentarians addressed personally"""
    font_config = FontConfiguration()
    css_path = module_path('onegov.pas', 'views/templates/settlement_pdf.css')
    with open(css_path) as f:
        css = CSS(string=f.read())

    subtitle = 'Einträge Journal'
    group_by: Literal['party', 'person']
    total_label: str

    if entity_type == 'commission' and isinstance(entity, PASCommission):
        settlement_data = _get_commission_settlement_data(
            settlement_run, request, entity
        )
        subtitle = f'Einträge Sitzungen: «{entity.name}»'
        group_by = 'party'
        total_label = f'Total {entity.name}'

    elif entity_type == 'party' and isinstance(entity, Party):
        settlement_data = _get_party_settlement_data(
            settlement_run, request, entity
        )
        group_by = 'person'
        total_label = f'Total {entity.name}'

    elif entity_type == 'all':
        settlement_data = _get_data_export_all(settlement_run, request)
        group_by = 'party'
        total_label = 'Total Parteien'
    else:
        raise ValueError(f'Unsupported entity type: {entity_type}')

    allowances = (
        PresidentialAllowanceCollection(
            request.session,
            settlement_run_id=settlement_run.id,
        )
        .query()
        .all()
    )

    if allowances:
        rate_set = get_current_rate_set(request.session, settlement_run)
        for a in allowances:
            compensation = calculate_compensation(
                a.amount,
                rate_set.cost_of_living_adjustment,
            )
            settlement_data.append(
                (
                    settlement_run.end,
                    a.parliamentarian,
                    LOHNART_ALLOWANCE_TEXT,
                    Decimal('0'),
                    compensation.base,
                    compensation.adjusted,
                )
            )

    totals = _settlement_totals(
        settlement_data,
        group_by,
        total_label,
        request.session,
        settlement_run.start,
        settlement_run.end,
    )

    html = _generate_settlement_html(
        settlement_data=settlement_data,
        totals=totals,
        subtitle=subtitle,
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
    result = []
    for attendence in attendences:
        is_president = is_commission_president(
            attendence.parliamentarian, commission.id, settlement_run
        )

        compensation = calculate_attendance_compensation(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=commission.type
        )

        result.append(
            (
                attendence.date,
                attendence.parliamentarian,
                request.translate(TYPES[attendence.type]),
                attendence.calculate_value(),
                compensation.base,
                compensation.adjusted,
            )
        )

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
           <div class="table-title">{subtitle}</div>
           <table class="journal-table">
               <thead>
                   <tr>
                       <th style="width:40pt">Datum</th>
                       <th style="width:90pt">Person</th>
                       <th style="width:252pt">Typ</th>
                       <th style="width:15pt">Wert</th>
                       <th style="width:35pt">CHF</th>
                       <th style="width:35pt">CHF + TZ</th>
                   </tr>
               </thead>
               <tbody>
   """

    for settlement_row in settlement_data:
        name = f'{settlement_row[1].first_name} {settlement_row[1].last_name}'
        html += f"""
           <tr>
               <td>{settlement_row[0].strftime('%d.%m.%Y')}</td>
               <td>{name}</td>
               <td>{settlement_row[2]}</td>
               <td class="numeric">{settlement_row[3]}</td>
               <td class="numeric">{format_swiss_number(
                   settlement_row[4])}</td>
               <td class="numeric">{format_swiss_number(
                   settlement_row[5])}</td>
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
               <td class="numeric">{format_swiss_number(
                   total_row[1])}</td>
               <td class="numeric">{format_swiss_number(
                   total_row[2])}</td>
               <td class="numeric">{format_swiss_number(
                   total_row[3])}</td>
               <td class="numeric">{format_swiss_number(
                   total_row[4])}</td>
               <td class="numeric">{format_swiss_number(
                   total_row[5])}</td>
           </tr>
       """

    # Handle last row separately with total-row class
    if totals:
        final_row = totals[-1]
        html += f"""
           <tr class="total-row">
               <td>{final_row[0]}</td>
               <td class="numeric">{format_swiss_number(
                   final_row[1])}</td>
               <td class="numeric">{format_swiss_number(
                   final_row[2])}</td>
               <td class="numeric">{format_swiss_number(
                   final_row[3])}</td>
               <td class="numeric">{format_swiss_number(
                   final_row[4])}</td>
               <td class="numeric">{format_swiss_number(
                   final_row[5])}</td>
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

    settlement_data: list[SettlementDataRow] = []

    for attendence in attendences.query():
        is_president = is_commission_president(
            attendence.parliamentarian, attendence, self
        )

        compensation = calculate_attendance_compensation(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            ),
        )

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
                compensation.base,
                compensation.adjusted,
            )
        )

    # Sort by date
    settlement_data.sort(key=itemgetter(0))
    return settlement_data


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

        compensation = calculate_attendance_compensation(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            )
        )

        type_desc = request.translate(TYPES[attendence.type])
        if attendence.commission:
            type_desc = f'{type_desc} - {attendence.commission.name}'

        result.append(
            (
                attendence.date,
                attendence.parliamentarian,
                type_desc,
                attendence.calculate_value(),
                compensation.base,
                compensation.adjusted,
            )
        )

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
            csv_string += ';'.join(row_strings) + '\n'

        # Encode to bytes with BOM for Excel compatibility
        csv_bytes = '\ufeff'.encode('utf-8') + csv_string.encode('utf-8')

        return Response(
            csv_bytes,
            content_type='text/csv; charset=utf-8',
            content_disposition=f'attachment; filename="{filename}"'
        )
    elif self.category == 'all-parliamentarians-zip':
        session = request.session
        parliamentarians = get_parliamentarians_with_settlements(
            session,
            self.settlement_run.start,
            self.settlement_run.end,
            settlement_run_id=self.settlement_run.id,
        )
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zf:
            for p in parliamentarians:
                pdf_bytes = generate_parliamentarian_settlement_pdf(
                    self.settlement_run, request, p
                )
                name = f'{p.last_name}_{p.first_name}'.replace(
                    ',', ' '
                ).replace('+', ' ')
                fname = normalize_for_filename(f'Parlamentarier_{name}')
                zf.writestr(f'{fname}.pdf', pdf_bytes)

        zip_buffer.seek(0)
        run_name = normalize_for_filename(self.settlement_run.name)
        filename = f'Parlamentarier_{run_name}.zip'
        return Response(
            zip_buffer.read(),
            content_type='application/zip',
            content_disposition=(f'attachment; filename="{filename}"'),
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
        name = self.entity.name.replace(',', ' ').replace('+', ' ')
        filename = normalize_for_filename(f'Partei_{name}')

    elif self.category == 'commission':
        assert isinstance(self.entity, PASCommission)

        pdf_bytes = generate_settlement_pdf(
            settlement_run=self.settlement_run,
            request=request,
            entity_type='commission',
            entity=self.entity,
        )
        name = self.entity.name.replace(',', ' ').replace('+', ' ')
        filename = normalize_for_filename(f'commission_{name}')

    elif self.category == 'parliamentarian':
        assert isinstance(self.entity, PASParliamentarian)
        pdf_bytes = generate_parliamentarian_settlement_pdf(
            self.settlement_run, request, self.entity
        )
        name = f'{self.entity.last_name}_{self.entity.first_name}'
        filename = normalize_for_filename(
            'Parlamentarier_' + name.replace(',', ' ').replace('+', ' ')
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
    name='toggle-close',
    request_method='POST',
    permission=Private
)
def toggle_close_settlement_run(
    self: SettlementRun,
    request: TownRequest
) -> Response:

    request.assert_valid_csrf_token()

    self.closed = not self.closed
    action = _('closed') if self.closed else _('reopened')
    request.success(
        _('Settlement run ${name} has been ${action}',
          mapping={'name': self.name, 'action': action})
    )

    return request.redirect(request.link(self))


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

    if self.closed:
        request.alert(
            _('Cannot delete closed settlement run. '
              'Please reopen it first.')
        )
        return

    collection = SettlementRunCollection(request.session)
    collection.delete(self)

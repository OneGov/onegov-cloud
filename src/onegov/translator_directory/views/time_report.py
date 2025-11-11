from __future__ import annotations

import csv
from io import StringIO
from webob import Response
from datetime import datetime

from onegov.core.security import Secret
from onegov.translator_directory import TranslatorDirectoryApp, _
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.layout import (
    TimeReportCollectionLayout,
    TimeReportLayout,
)
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from collections.abc import Iterator


@TranslatorDirectoryApp.html(
    model=TimeReportCollection,
    template='time_reports.pt',
    permission=Secret,
)
def view_time_reports(
    self: TimeReportCollection,
    request: TranslatorAppRequest,
) -> RenderData:

    layout = TimeReportCollectionLayout(self, request)

    now = datetime.now()
    current_year = now.year
    default_month = now.month
    default_year = now.year

    months = [
        (1, request.translate(_('January'))),
        (2, request.translate(_('February'))),
        (3, request.translate(_('March'))),
        (4, request.translate(_('April'))),
        (5, request.translate(_('May'))),
        (6, request.translate(_('June'))),
        (7, request.translate(_('July'))),
        (8, request.translate(_('August'))),
        (9, request.translate(_('September'))),
        (10, request.translate(_('October'))),
        (11, request.translate(_('November'))),
        (12, request.translate(_('December'))),
    ]

    years = [current_year, current_year - 1, current_year - 2]
    export_url = request.link(self, 'export-accounting')

    return {
        'layout': layout,
        'model': self,
        'title': layout.title,
        'reports': self.batch,
        'months': months,
        'years': years,
        'default_month': default_month,
        'default_year': default_year,
        'export_url': export_url,
    }


@TranslatorDirectoryApp.html(
    model=TranslatorTimeReport,
    template='time_report.pt',
    permission=Secret,
)
def view_time_report(
    self: TranslatorTimeReport,
    request: TranslatorAppRequest,
) -> RenderData:

    layout = TimeReportLayout(self, request)

    return {
        'layout': layout,
        'model': self,
        'title': _('Time Report'),
        'report': self,
    }


def generate_accounting_export_rows(
    reports: list[TranslatorTimeReport],
) -> Iterator[list[str]]:
    """Generate CSV rows for accounting export in the required format."""
    from decimal import Decimal

    for report in reports:
        translator = report.translator
        assert translator.pers_id is not None
        pers_nr = str(translator.pers_id)
        date_str = report.assignment_date.strftime('%d.%m.%Y')

        duration_hours = str(report.duration_hours)
        effective_rate = report.hourly_rate * (
            1 + report.effective_surcharge_percentage / Decimal(100)
        )
        effective_rate_str = str(effective_rate.quantize(Decimal('0.01')))
        travel_and_meal = report.travel_compensation + report.meal_allowance
        travel_and_meal_str = str(travel_and_meal)

        row_2603 = [
            'L001',
            pers_nr,
            date_str,
            '0',
            '2603',
            '0',
            '',
            'VWG Entschädigung Dolmetscher',
            duration_hours,
            '1',
            effective_rate_str,
            '1',
            '0',
            '0',
            '0',
            '0',
            '0',
            '0',
            '0',
            '1',
            '0',
            '',
            '0',
            '0',
            '0',
            '',
            '',
            '',
            '',
            '',
            '',
            'L001',
        ]
        yield row_2603

        if travel_and_meal > 0:
            row_8102 = [
                'L001',
                pers_nr,
                date_str,
                '0',
                '8102',
                '0',
                '',
                'VWG Reisespesen Dolmetscher',
                travel_and_meal_str,
                '1',
                '0',
                '0',
                '0',
                '0',
                '0',
                '0',
                '0',
                '0',
                '0',
                '1',
                '0',
                '',
                '0',
                '0',
                '0',
                '',
                '',
                '',
                '',
                '',
                '',
                'L001',
            ]
            yield row_8102


@TranslatorDirectoryApp.view(
    model=TimeReportCollection,
    name='export-accounting',
    permission=Secret,
    request_method='POST',
)
def export_accounting_csv(
    self: TimeReportCollection,
    request: TranslatorAppRequest,
) -> Response:
    """Export confirmed time reports as CSV for accounting."""

    try:
        year = int(str(request.POST.get('year', '0')))
        month = int(str(request.POST.get('month', '0')))
    except (ValueError, TypeError):
        request.message(_('Invalid form data'), 'warning')
        return request.redirect(request.link(self))

    if not (1 <= month <= 12) or year < 2000:
        request.message(_('Invalid form data'), 'warning')
        return request.redirect(request.link(self))

    reports = list(self.for_accounting_export(year, month))

    if not reports:
        request.message(
            _(
                'No confirmed time reports found for ${month}/${year}',
                mapping={'month': month, 'year': year},
            ),
            'warning',
        )
        return request.redirect(request.link(self))

    missing_pers_id = [r for r in reports if not r.translator.pers_id]
    if missing_pers_id:
        translator_names = ', '.join(
            r.translator.title for r in missing_pers_id
        )
        request.message(
            _(
                'Cannot export: The following translators are missing '
                'a personnel number (Personal-Nr.): ${names}',
                mapping={'names': translator_names},
            ),
            'warning',
        )
        return request.redirect(request.link(self))

    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    header = [
        'PreEntry',
        'Personal-Nr.',
        'Periodendatum',
        'Periodennummer',
        'Lohnart',
        'Belegnummer',
        'Währung',
        'Text Lohnart',
        'Anzahl',
        'Mutationscode Anzahl',
        'Ansatz',
        'Mutationscode Ansatz',
        'Kostenstelle 1',
        'Kostenstelle 2',
        'Freie Nummer',
        'Funktion Gemeinde',
        'Art Gemeinde',
        'Subnummer Referenz',
        'GB zum Verbuchen der Vorerfassung',
        'AnsV-Nr.',
        'Wiederkehrende Vorerfassung',
        'Mehrwertsteuer-Code',
        'Fibu-Konto',
        'Freie Nummer 1',
        'Freie Nummer 2',
        'Freier Text 1',
        'Freier Text 2',
        'Freies Datum 1',
        'Kommentar',
        'Benutzername',
        'Mutationsdatum',
        'PostEntry',
    ]
    writer.writerow(header)

    for row in generate_accounting_export_rows(reports):
        writer.writerow(row)

    csv_content = output.getvalue()
    csv_bytes = csv_content.encode('iso-8859-1')
    filename = f'translator_export_{year}_{month:02d}.csv'
    response = Response(csv_bytes)
    response.content_type = 'text/csv; charset=iso-8859-1'
    response.content_disposition = f'attachment; filename="{filename}"'

    return response

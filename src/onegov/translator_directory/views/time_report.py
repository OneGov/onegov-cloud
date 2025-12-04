from __future__ import annotations


import csv
import json
from onegov.translator_directory.i18n import _
from io import StringIO
from webob import Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from onegov.core.mail import Attachment
from onegov.core.utils import module_path
from onegov.translator_directory.qrbill import (
    generate_translator_qr_bill,
    is_valid_iban,
)
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration,
)

from onegov.core.security import Private, Personal
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.org.mail import send_ticket_mail
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.forms.time_report import (
    TranslatorTimeReportForm,
)
from onegov.translator_directory.generate_docx import gendered_greeting
from onegov.translator_directory.layout import (
    TimeReportCollectionLayout,
    TimeReportLayout,
    TranslatorLayout,
)
from onegov.translator_directory.models.ticket import (
    TimeReportTicket,
    TimeReportHandler,
)
from onegov.translator_directory.constants import ASSIGNMENT_LOCATIONS
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.org.models.message import TimeReportMessage
from onegov.user import User
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.models.translator import Translator
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from collections.abc import Iterator
    from webob import Response as BaseResponse


@TranslatorDirectoryApp.html(
    model=TimeReportCollection,
    template='time_reports.pt',
    permission=Private,
)
def view_time_reports(
    self: TimeReportCollection,
    request: TranslatorAppRequest,
) -> RenderData:

    layout = TimeReportCollectionLayout(self, request)

    now = datetime.now()
    current_year = now.year
    last_month = now - relativedelta(months=1)
    default_month = last_month.month
    default_year = last_month.year

    selected_month = self.month if self.month is not None else None
    selected_year = self.year if self.year is not None else None

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

    report_ids = [str(report.id) for report in self.batch]
    tickets = (
        request.session.query(TimeReportTicket)
        .filter(
            TimeReportTicket.handler_data['handler_data'][
                'time_report_id'
            ].astext.in_(report_ids)
        )
        .all()
    )
    report_tickets = {
        ticket.handler_data['handler_data']['time_report_id']: ticket
        for ticket in tickets
    }

    return {
        'layout': layout,
        'model': self,
        'title': layout.title,
        'reports': self.batch,
        'report_tickets': report_tickets,
        'months': months,
        'years': years,
        'default_month': default_month,
        'default_year': default_year,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'export_url': export_url,
    }


@TranslatorDirectoryApp.form(
    model=TranslatorTimeReport,
    name='edit',
    template='form.pt',
    permission=Personal,
    form=TranslatorTimeReportForm,
)
def edit_time_report(
    self: TranslatorTimeReport,
    request: TranslatorAppRequest,
    form: TranslatorTimeReportForm,
) -> RenderData | BaseResponse:
    if self.status != 'pending':
        request.alert(_('Only pending time reports can be edited'))
        ticket = self.get_ticket(request.session)
        if ticket:
            return request.redirect(request.link(ticket))
        return request.redirect(
            request.link(TimeReportCollection(request.app))
        )

    layout = TimeReportLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Time report updated successfully'))
        ticket = self.get_ticket(request.session)
        if ticket:
            TimeReportMessage.create(
                ticket=ticket,
                request=request,
                change=request.translate(_('Edit Time Report')),
            )
            return request.redirect(request.link(ticket))
        return request.redirect(
            request.link(TimeReportCollection(request.app))
        )

    if not form.errors:
        form.process(obj=self)

    return {
        'layout': layout,
        'model': self,
        'title': _('Edit Time Report'),
        'form': form,
        'button_text': _('Update Time Report'),
    }


def show_warning_for_intercooler(
    request: TranslatorAppRequest, message: str
) -> BaseResponse:
    """Using just a normal request.warning gets suppressed.
    So we use this.
    """

    translated_message = request.translate(message)

    @request.after
    def add_warning_headers(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'show-alert')
        response.headers.add(
            'X-IC-Trigger-Data',
            json.dumps(
                {'type': 'warning', 'message': translated_message},
                ensure_ascii=True,
            ),
        )

    return Response()


@TranslatorDirectoryApp.view(
    model=TimeReportTicket,
    name='accept-time-report',
    permission=Private,
    request_method='POST',
)
def accept_time_report(
    self: TimeReportTicket, request: TranslatorAppRequest
) -> BaseResponse:
    """Accept time report."""

    request.assert_valid_csrf_token()

    handler = self.handler
    assert hasattr(handler, 'time_report')
    if not handler.time_report:
        return show_warning_for_intercooler(
            request, _('Time report not found')
        )

    time_report = handler.time_report
    translator = time_report.translator

    if translator and translator.self_employed:
        if not is_valid_iban(translator.iban):
            return show_warning_for_intercooler(
                request,
                _(
                    'Cannot accept time report: '
                    'Self-employed translator must have valid IBAN'
                ),
            )

        if not all([translator.address, translator.zip_code, translator.city]):
            return show_warning_for_intercooler(
                request,
                _(
                    'Cannot accept time report: '
                    'Self-employed translator must have complete address'
                ),
            )

    time_report.status = 'confirmed'
    handler.data['state'] = 'accepted'

    if translator and translator.email:
        call_to_action_link = request.link(self)

        pdf_bytes = generate_time_report_pdf_bytes(
            time_report, translator, request
        )
        filename = (
            f'Zeiterfassung_{translator.last_name}_'
            f'{time_report.assignment_date.strftime("%Y%m%d")}.pdf'
        )

        pdf_attachment = Attachment(
            filename=filename,
            content=pdf_bytes,
            content_type='application/pdf',
        )

        travel_info = None
        if (time_report.assignment_location
                and time_report.travel_distance):
            location_name, _address = ASSIGNMENT_LOCATIONS.get(
                time_report.assignment_location,
                (time_report.assignment_location, '')
            )
            translator_address = (
                f'{translator.address}, '
                f'{translator.zip_code} {translator.city}'
            )
            travel_info = {
                'from_address': translator_address,
                'to_location': location_name,
                'distance': time_report.travel_distance
            }

        send_ticket_mail(
            request=request,
            template='mail_time_report_accepted.pt',
            subject=_('Time report accepted'),
            ticket=self,
            receivers=(translator.email,),
            content={
                'model': self,
                'translator': translator,
                'time_report': time_report,
                'call_to_action_link': call_to_action_link,
                'travel_info': travel_info,
            },
            attachments=[pdf_attachment],
        )

    request.success(_('Time report accepted'))
    return request.redirect(request.link(self))


def generate_accounting_export_rows(
    reports: list[TranslatorTimeReport],
) -> Iterator[list[str]]:
    """Generate CSV rows for accounting export in the required format."""

    for report in reports:
        translator = report.translator
        # the view has checked for missing pers_id before
        assert translator.pers_id is not None
        pers_nr = str(translator.pers_id)
        date_str = report.assignment_date.strftime('%d.%m.%Y')

        duration_hours = str(report.duration_hours)

        # Calculate effective rate from actual compensation
        # (since we can't use a simple percentage with partial night work)
        breakdown = report.calculate_compensation_breakdown()
        if report.duration_hours > 0:
            effective_rate = breakdown['subtotal'] / report.duration_hours
        else:
            effective_rate = report.hourly_rate
        effective_rate_str = str(effective_rate.quantize(Decimal('0.01')))

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

        if report.travel_compensation > 0:
            row_8102_travel = [
                'L001',
                pers_nr,
                date_str,
                '0',
                '8102',
                '0',
                '',
                'VWG Reisespesen Dolmetscher',
                str(report.travel_compensation),
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
            yield row_8102_travel

        if report.meal_allowance > 0:
            row_8102_meal = [
                'L001',
                pers_nr,
                date_str,
                '0',
                '8102',
                '0',
                '',
                'VWG Reisespesen Dolmetscher',  # Verpflegung
                str(report.meal_allowance),
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
            yield row_8102_meal


@TranslatorDirectoryApp.view(
    model=TimeReportCollection,
    name='export-accounting',
    permission=Private,
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

    confirmed_reports = list(self.for_accounting_export(year, month))
    if not confirmed_reports:
        request.message(
            _(
                'No confirmed time reports found for ${month}/${year}',
                mapping={'month': month, 'year': year},
            ),
            'warning',
        )
        return request.redirect(request.link(self))

    missing_pers_id = [
        r for r in confirmed_reports if not r.translator.pers_id
    ]
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

    # Header row MUST NOT be included: the accounting system will reject
    # the import if a header is present. Kept here for documentation and
    # debugging purposes.
    # header = [
    #     'PreEntry',
    #     'Personal-Nr.',
    #     'Periodendatum',
    #     'Periodennummer',
    #     'Lohnart',
    #     'Belegnummer',
    #     'Währung',
    #     'Text Lohnart',
    #     'Anzahl',
    #     'Mutationscode Anzahl',
    #     'Ansatz',
    #     'Mutationscode Ansatz',
    #     'Kostenstelle 1',
    #     'Kostenstelle 2',
    #     'Freie Nummer',
    #     'Funktion Gemeinde',
    #     'Art Gemeinde',
    #     'Subnummer Referenz',
    #     'GB zum Verbuchen der Vorerfassung',
    #     'AnsV-Nr.',
    #     'Wiederkehrende Vorerfassung',
    #     'Mehrwertsteuer-Code',
    #     'Fibu-Konto',
    #     'Freie Nummer 1',
    #     'Freie Nummer 2',
    #     'Freier Text 1',
    #     'Freier Text 2',
    #     'Freies Datum 1',
    #     'Kommentar',
    #     'Benutzername',
    #     'Mutationsdatum',
    #     'PostEntry',
    # ]
    # writer.writerow(header)

    for row in generate_accounting_export_rows(confirmed_reports):
        writer.writerow(row)

    csv_content = output.getvalue()
    csv_bytes = csv_content.encode('iso-8859-1')
    filename = f'translator_export_{year}_{month:02d}.csv'
    response = Response(csv_bytes)
    response.content_type = 'text/csv; charset=iso-8859-1'
    response.content_disposition = f'attachment; filename="{filename}"'
    return response


def generate_time_report_pdf_bytes(
    time_report: TranslatorTimeReport,
    translator: Translator,
    request: TranslatorAppRequest,
) -> bytes:
    layout = TranslatorLayout(translator, request)
    font_config = FontConfiguration()
    css_path = module_path(
        'onegov.translator_directory', 'views/templates/time_report_pdf.css'
    )
    with open(css_path) as f:
        css = CSS(string=f.read(), font_config=font_config)

    # Get ticket number for display
    ticket = time_report.get_ticket(request.session)
    ticket_number = ticket.number if ticket else None

    assignment_date_display = layout.format_date(
        time_report.assignment_date, 'date'
    )

    if time_report.start and time_report.end:
        start_date = time_report.start.date()
        end_date = time_report.end.date()
        start_time = layout.format_date(time_report.start, 'time')
        end_time = layout.format_date(time_report.end, 'time')

        if start_date != end_date:
            assignment_date_display = (
                f'{layout.format_date(start_date, "date")} {start_time} - '
                f'{layout.format_date(end_date, "date")} {end_time}'
            )
        else:
            assignment_date_display = (
                f'{layout.format_date(start_date, "date")}, '
                f'{start_time} - {end_time}'
            )

    today = datetime.now()
    letter_date = f'Schaffhausen, {layout.format_date(today, "date_long")}'

    match translator.gender:
        case 'M':
            title = 'Herr'
        case 'F':
            title = 'Frau'
        case _:
            title = 'Herr/Frau'

    salutation = f'{gendered_greeting(translator)} {translator.last_name}'
    translator_name = f'{translator.first_name} {translator.last_name}'

    duration_text = (
        f'{time_report.duration_hours} Stunde'
        if time_report.duration_hours == 1
        else f'{time_report.duration_hours} Stunden'
    )

    logo_url = request.app.org.logo_url if request.app.org.logo_url else None
    html_content = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
    """

    html_content += """
            <div class="header-row">
                <div class="logo">
    """

    if logo_url:
        html_content += f"""
                    <img src="{logo_url}" alt="Logo" />
        """

    html_content += f"""
                </div>
                <div class="letter-date">
                    {letter_date}
                </div>
            </div>

            <div class="translator-info">
                <p>
                    {title}<br>
                    <strong>{translator_name}</strong><br>
    """

    if translator.address:
        html_content += f'                    {translator.address}<br>\n'
    if translator.zip_code and translator.city:
        html_content += (
            f'                    {translator.zip_code} '
            f'{translator.city}<br>\n'
        )

    html_content += f"""
                </p>
            </div>

            <div class="section-title">
                <h2>Dolmetscher-Entschädigungen</h2>
            </div>

            <div class="salutation">
                {salutation}
            </div>

            <div class="intro-text">
                <p>
                    Ihre Rapportierung wurde durch das Rechnungswesen
                    bestätigt.
                </p>
            </div>

            <div class="assignment-info">
                <p>
                    <strong>
                        {request.translate(_('Assignment Date'))}:
                    </strong>
                    {assignment_date_display}
                </p>
    """

    if ticket_number:
        html_content += f"""
                <p>
                    <strong>
                        {request.translate(_('Ticket Number'))}:
                    </strong>
                    {ticket_number}
                </p>
    """

    html_content += """
            </div>
    """

    html_content += f"""
            <div class="compensation">
                <table class="compensation-table">
                    <tr>
                        <td class="label">
                            {request.translate(_('Hourly Rate'))}:
                        </td>
                        <td class="amount">
                            {layout.format_currency(time_report.hourly_rate)}
                        </td>
                    </tr>
    """

    # Use centralized calculation from model
    breakdown = time_report.calculate_compensation_breakdown()

    # Show day/night hours breakdown if there are night hours
    if time_report.night_minutes > 0:
        day_hours = time_report.day_hours_decimal
        night_hours = time_report.night_hours_decimal

        day_hours_text = (
            f'{day_hours} Stunde' if day_hours == 1
            else f'{day_hours} Stunden'
        )
        night_hours_text = (
            f'{night_hours} Stunde' if night_hours == 1
            else f'{night_hours} Stunden'
        )

        day_rate = layout.format_currency(time_report.hourly_rate)
        night_rate = layout.format_currency(
            time_report.night_hourly_rate
        )
        html_content += f"""
                    <tr>
                        <td class="label">
                            Tagstunden ({day_rate}
                            × {day_hours_text}):
                        </td>
                        <td class="amount">
                            {layout.format_currency(breakdown['day_pay'])}
                        </td>
                    </tr>
                    <tr>
                        <td class="label">
                            Nachtstunden 20-06 Uhr ({night_rate}
                            × {night_hours_text}, +50%):
                        </td>
                        <td class="amount">
                            {layout.format_currency(breakdown['night_pay'])}
                        </td>
                    </tr>
        """
    else:
        # No night hours, show simple day pay
        html_content += f"""
                    <tr>
                        <td class="label">
                            {request.translate(_('Base pay'))}
                            ({layout.format_currency(time_report.hourly_rate)}
                            × {duration_text}):
                        </td>
                        <td class="amount">
                            {layout.format_currency(breakdown['day_pay'])}
                        </td>
                    </tr>
        """

    # Show weekend surcharge if applicable
    if breakdown['weekend_surcharge'] > 0:
        # Calculate actual weekend hours that get the surcharge (non-night)
        weekend_holiday_hours = time_report.weekend_holiday_hours_decimal
        night_hours = time_report.night_hours_decimal
        weekend_non_night_hours = weekend_holiday_hours - min(
            weekend_holiday_hours, night_hours
        )
        weekend_hours_text = (
            f'{weekend_non_night_hours} Stunde'
            if weekend_non_night_hours == 1
            else f'{weekend_non_night_hours} Stunden'
        )
        html_content += f"""
                    <tr>
                        <td class="label">
                            Zuschlag WE ({weekend_hours_text}, +25%):
                        </td>
                        <td class="amount">
                            {layout.format_currency(breakdown['weekend_surcharge'])}
                        </td>
                    </tr>
        """

    # Show urgent surcharge if applicable
    if breakdown['urgent_surcharge'] > 0:
        urgent_label = request.translate(_('Exceptionally urgent'))
        html_content += f"""
                    <tr>
                        <td class="label">
                            {urgent_label} (+25%):
                        </td>
                        <td class="amount">
                            {layout.format_currency(breakdown['urgent_surcharge'])}
                        </td>
                    </tr>
        """

    # Show break time deduction if applicable
    if breakdown['break_deduction'] > 0:
        break_hours = time_report.break_time_hours
        html_content += f"""
                    <tr>
                        <td class="label">
                            Pausenzeit (
                            {layout.format_currency(time_report.hourly_rate)}
                            × -{break_hours} Stunden):
                        </td>
                        <td class="amount">
                            -{layout.format_currency(breakdown['break_deduction'])}
                        </td>
                    </tr>
        """

    html_content += f"""
                    <tr class="subtotal">
                        <td class="label">
                            <strong>
                                {request.translate(
                                    _('Subtotal (work compensation)')
                                )}:
                            </strong>
                        </td>
                        <td class="amount">
                            <strong>
                                {layout.format_currency(breakdown['adjusted_subtotal'])}
                            </strong>
                        </td>
                    </tr>
    """

    travel_label = request.translate(_('Travel'))
    if time_report.assignment_location:
        location_name, _address = ASSIGNMENT_LOCATIONS.get(
            time_report.assignment_location,
            (time_report.assignment_location, '')
        )
        translator_address = (
            f'{translator.address}, '
            f'{translator.zip_code} {translator.city}'
        )
        if time_report.travel_distance:
            travel_label = (
                f"{request.translate(_('Travel'))} "
                f"({request.translate(_('from'))} {translator_address} "
                f"{request.translate(_('to'))} {location_name}, "
                f"{time_report.travel_distance} km \u00d7 2)"
            )
        else:
            travel_label = (
                f"{request.translate(_('Travel'))} "
                f"({request.translate(_('from'))} {translator_address} "
                f"{request.translate(_('to'))} {location_name})"
            )
    elif translator.drive_distance:
        translator_address = (
            f'{translator.address}, '
            f'{translator.zip_code} {translator.city}'
        )
        travel_label = (
            f"{request.translate(_('Travel'))} "
            f"({request.translate(_('from'))} {translator_address}, "
            f"{translator.drive_distance} km \u00d7 2)"
        )

    html_content += f"""
                    <tr>
                        <td class="label">{travel_label}:</td>
                        <td class="amount">
                            {layout.format_currency(
                                time_report.travel_compensation
                            )}
                        </td>
                    </tr>
    """

    if time_report.meal_allowance:
        meal_label = request.translate(_('Meal Allowance (6+ hours)'))
        html_content += f"""
                    <tr>
                        <td class="label">
                            {meal_label}:
                        </td>
                        <td class="amount">
                            {layout.format_currency(time_report.meal_allowance)}
                        </td>
                    </tr>
        """

    html_content += f"""
                    <tr class="total">
                        <td class="label">
                            <strong>{request.translate(_('Total'))}</strong>:
                        </td>
                        <td class="amount">
                            <strong>
                                {layout.format_currency(breakdown['total'])}
                            </strong>
                        </td>
                    </tr>
                </table>
            </div>
    """

    accountant_email = request.app.accountant_email
    accountant_name = ''
    if (
        accountant_email
        and (
            accountant_user := request.session.query(User)
            .filter(func.lower(User.username) == accountant_email.lower())
            .first()
        )
        and accountant_user.realname
    ):
        accountant_name = accountant_user.realname

    closing_text = 'Mit freundlichen Grüssen<br><br>Rechnungsbüro'
    if accountant_name:
        closing_text = (
            f'Mit freundlichen Grüssen<br><br>Rechnungsbüro<br>'
            f'{accountant_name}'
        )

    html_content += f"""
            <div class="thank-you">
                <p>
                    Wir danken Ihnen für Ihre Einsätze und bitten um
                    entsprechende Kenntnisnahme.
                </p>
            </div>

            <div class="closing">
                <p>
                    {closing_text}
                </p>
            </div>
    """

    html_content += """
        </body>
        </html>
    """

    pdf_bytes = HTML(string=html_content).write_pdf(
        stylesheets=[css], font_config=font_config
    )

    return pdf_bytes


@TranslatorDirectoryApp.view(
    model=TimeReportTicket,
    name='time-report-pdf-for-translator',
    permission=Private,
)
def generate_time_report_pdf_for_translator(
    self: TimeReportTicket,
    request: TranslatorAppRequest,
) -> Response:
    handler = self.handler
    assert isinstance(handler, TimeReportHandler)
    if not handler.time_report or not handler.translator:
        request.alert(_('Time report not found'))
        return request.redirect(request.link(self))

    time_report = handler.time_report
    translator = handler.translator
    pdf_bytes = generate_time_report_pdf_bytes(
        time_report, translator, request
    )
    filename = (
        f'Zeiterfassung_{translator.last_name}_'
        f'{time_report.assignment_date.strftime("%Y%m%d")}.pdf'
    )

    response = Response(pdf_bytes)
    response.content_type = 'application/pdf'
    response.content_disposition = f'inline; filename="{filename}"'

    return response


@TranslatorDirectoryApp.view(
    model=TimeReportTicket,
    name='qr-bill-pdf',
    permission=Private,
)
def generate_qr_bill_pdf_for_translator(
    self: TimeReportTicket,
    request: TranslatorAppRequest,
) -> Response:
    handler = self.handler
    assert isinstance(handler, TimeReportHandler)
    if not handler.time_report or not handler.translator:
        request.alert(_('Time report not found'))
        return request.redirect(request.link(self))

    time_report = handler.time_report
    translator = handler.translator

    if not translator.self_employed:
        request.alert(_('QR bill only available for self-employed'))
        return request.redirect(request.link(self))

    if time_report.status != 'confirmed':
        request.alert(_('QR bill only available for confirmed reports'))
        return request.redirect(request.link(self))

    qr_bill_bytes = generate_translator_qr_bill(
        translator, time_report, request
    )

    if not qr_bill_bytes:
        request.alert(_('Could not generate QR bill'))
        return request.redirect(request.link(self))

    filename = (
        f'QR_Rechnung_{translator.last_name}_'
        f'{time_report.assignment_date.strftime("%Y%m%d")}.pdf'
    )

    response = Response(qr_bill_bytes)
    response.content_type = 'application/pdf'
    response.content_disposition = f'inline; filename="{filename}"'
    return response

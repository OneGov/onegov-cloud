from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from onegov.file import File
from morepath import redirect
from sedate import replace_timezone
from datetime import datetime
from morepath.request import Response
from sedate import utcnow
from onegov.core.custom import json
from onegov.core.security import Secret, Personal, Private
from onegov.core.templates import render_template
from onegov.file.integration import get_file
from onegov.org.layout import DefaultMailLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import GeneralFileCollection
from onegov.org.models import TicketMessage
from onegov.org.utils import emails_for_new_ticket
from onegov.ticket import TicketCollection
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory.utils import (
    get_accountant_emails_for_finanzstelle
)
from onegov.translator_directory.constants import (
    PROFESSIONAL_GUILDS, INTERPRETING_TYPES, ADMISSIONS, GENDERS, GENDER_MAP)
from onegov.translator_directory.forms.mutation import TranslatorMutationForm
from onegov.translator_directory.forms.time_report import (
    TranslatorTimeReportForm,
)
from onegov.translator_directory.forms.translator import (
    TranslatorForm, TranslatorSearchForm,
    EditorTranslatorForm, MailTemplatesForm)
from onegov.translator_directory.generate_docx import (
    fill_docx_with_variables, signature_for_mail_templates,
    parse_from_filename, get_ticket_nr_of_translator)
from onegov.translator_directory.layout import (
    AddTranslatorLayout,
    TranslatorCollectionLayout,
    TranslatorLayout,
    EditTranslatorLayout,
    ReportTranslatorChangesLayout,
    MailTemplatesLayout,
)
from onegov.translator_directory.models.time_report import TranslatorTimeReport
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.utils import country_code_to_name

from uuid import uuid4
from xlsxwriter import Workbook
from docx.image.exceptions import UnrecognizedImageError
from webob.exc import HTTPForbidden


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date, datetime
    from collections.abc import Iterable
    from onegov.core.types import RenderData
    from onegov.translator_directory.models.certificate import (
        LanguageCertificate)
    from onegov.translator_directory.models.language import Language
    from onegov.translator_directory.models.translator import (
        AdmissionState, Gender, InterpretingType)
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response as BaseResponse


@TranslatorDirectoryApp.form(
    model=TranslatorCollection,
    template='form.pt',
    name='new',
    form=TranslatorForm,
    permission=Secret
)
def add_new_translator(
    self: TranslatorCollection,
    request: TranslatorAppRequest,
    form: TranslatorForm
) -> RenderData | BaseResponse:

    form.delete_field('date_of_decision')
    form.delete_field('for_admins_only')
    form.delete_field('proof_of_preconditions')

    if form.submitted(request):
        data = form.get_useful_data()
        translator = self.add(**data)
        request.success(_('Added a new translator'))

        if translator.user:
            subject = request.translate(
                _('An account was created for you')
            )
            content = render_template('mail_new_user.pt', request, {
                'user': translator.user,
                'org': request.app.org,
                'layout': DefaultMailLayout(translator.user, request),
                'title': subject
            })
            request.app.send_transactional_email(
                subject=subject,
                receivers=(translator.user.username, ),
                content=content,
            )
            request.success(_('Activation E-Mail sent'))

        return request.redirect(request.link(translator))

    layout = AddTranslatorLayout(self, request)
    layout.edit_mode = True

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': layout.title
    }


@TranslatorDirectoryApp.form(
    model=TranslatorCollection,
    template='translators.pt',
    permission=Personal,
    form=TranslatorSearchForm
)
def view_translators(
    self: TranslatorCollection,
    request: TranslatorAppRequest,
    form: TranslatorSearchForm
) -> RenderData | BaseResponse:

    layout = TranslatorCollectionLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        return request.redirect(request.link(self))

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'model': self,
        'title': layout.title,
        'form': form,
        'results': self.batch,
        'button_text': _('Submit Search')
    }


@TranslatorDirectoryApp.view(
    model=TranslatorCollection,
    permission=Secret,
    name='export'
)
def export_translator_directory(
    self: TranslatorCollection,
    request: TranslatorAppRequest
) -> Response:

    output = BytesIO()
    workbook = Workbook(output)

    def format_date(dt: datetime | date | None) -> str:
        if not dt:
            return ''
        return dt.strftime('%Y-%m-%d')

    def format_iterable(listlike: Iterable[str]) -> str:
        return '|'.join(listlike) if listlike else ''

    def format_languages(
        langs: Iterable[Language | LanguageCertificate]
    ) -> str:
        return format_iterable(la.name for la in langs)

    def format_guilds(guilds: Iterable[str]) -> str:
        return format_iterable(
            request.translate(PROFESSIONAL_GUILDS[s])
            if s in PROFESSIONAL_GUILDS else s
            for s in guilds
        )

    def format_interpreting_types(types: Iterable[InterpretingType]) -> str:
        return format_iterable(
            request.translate(INTERPRETING_TYPES[t]) for t in types
        )

    def format_admission(admission: AdmissionState | None) -> str:
        if not admission:
            return ''
        return request.translate(ADMISSIONS[admission])

    def format_gender(gender: Gender | None) -> str:
        if not gender:
            return ''
        return request.translate(GENDERS[gender])

    def format_nationalities(nationalities: list[str] | None) -> str:
        mapping = country_code_to_name(request.locale)
        if not nationalities:
            return ''
        return ', '.join(mapping[n] for n in nationalities)

    worksheet = workbook.add_worksheet(
        request.translate(_('Translator directory'))
    )
    worksheet.write_row(0, 0, (
        request.translate(_('Personal ID')),
        request.translate(_('Admission')),
        request.translate(_('Withholding tax')),
        request.translate(_('Self-employed')),
        request.translate(_('Last name')),
        request.translate(_('First name')),
        request.translate(_('Gender')),
        request.translate(_('Date of birth')),
        request.translate(_('Nationality(ies)')),
        request.translate(_('Location')),
        request.translate(_('Address')),
        request.translate(_('Zip Code')),
        request.translate(_('City')),
        request.translate(_('Drive distance')),
        request.translate(_('Swiss social security number')),
        request.translate(_('Bank name')),
        request.translate(_('Bank address')),
        request.translate(_('Account owner')),
        request.translate(_('IBAN')),
        request.translate(_('Email')),
        request.translate(_('Private Phone Number')),
        request.translate(_('Mobile Phone Number')),
        request.translate(_('Office Phone Number')),
        request.translate(_('Availability')),
        request.translate(_('Comments on possible field of application')),
        request.translate(_('Name reveal confirmation')),
        request.translate(_('Date of application')),
        request.translate(_('Date of decision')),
        request.translate(_('Mother tongues')),
        request.translate(_('Spoken languages')),
        request.translate(_('Written languages')),
        request.translate(_('Monitoring languages')),
        request.translate(_('Learned profession')),
        request.translate(_('Current professional activity')),
        request.translate(_('Expertise by professional guild')),
        request.translate(_('Expertise by interpreting type')),
        request.translate(_('Proof of preconditions')),
        request.translate(_('Agency references')),
        request.translate(_('Education as interpreter')),
        request.translate(_('Certificates')),
        request.translate(_('Comments')),
        request.translate(_('Hidden')),
    ))

    for ix, trs in enumerate(self.query()):
        worksheet.write_row(ix + 1, 0, (
            trs.pers_id or '',
            format_admission(trs.admission),
            trs.withholding_tax and 1 or 0,
            trs.self_employed and 1 or 0,
            trs.last_name,
            trs.first_name,
            format_gender(trs.gender),
            format_date(trs.date_of_birth),
            format_nationalities(trs.nationalities),
            json.dumps(trs.coordinates),
            trs.address or '',
            trs.zip_code or '',
            trs.city or '',
            trs.drive_distance or '',
            trs.social_sec_number or '',
            trs.bank_name or '',
            trs.bank_address or '',
            trs.account_owner or '',
            trs.iban or '',
            trs.email or '',
            trs.tel_private or '',
            trs.tel_mobile or '',
            trs.tel_office or '',
            trs.availability or '',
            trs.operation_comments or '',
            trs.confirm_name_reveal and 1 or 0,
            format_date(trs.date_of_application),
            format_date(trs.date_of_decision),
            format_languages(trs.mother_tongues),
            format_languages(trs.spoken_languages),
            format_languages(trs.written_languages),
            format_languages(trs.monitoring_languages),
            trs.profession or '',
            trs.occupation or '',
            format_guilds(trs.expertise_professional_guilds_all),
            format_interpreting_types(trs.expertise_interpreting_types),
            trs.proof_of_preconditions or '',
            trs.agency_references or '',
            trs.education_as_interpreter and 1 or 0,
            format_languages(trs.certificates),
            trs.comments or '',
            trs.for_admins_only and 1 or 0
        ))

    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}.xlsx'.format(
        request.translate(_('Translator directory')).lower(),
        utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response


@TranslatorDirectoryApp.html(
    model=Translator,
    template='translator.pt',
    permission=Personal
)
def view_translator(
    self: Translator,
    request: TranslatorAppRequest
) -> RenderData:
    layout = TranslatorLayout(self, request)
    if layout.translator_data_outdated():
        request.warning(_(
            'Is your information still up do date? Please check and either '
            'modify or confirm using the buttons above.'))

    return {
        'layout': layout,
        'model': self,
        'title': self.title,
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='form.pt',
    name='edit',
    form=TranslatorForm,
    permission=Secret
)
def edit_translator(
    self: Translator,
    request: TranslatorAppRequest,
    form: TranslatorForm
) -> RenderData | BaseResponse:

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))
    if not form.errors:
        form.process(
            obj=self,
            data={
                attr: form.get_ids(self, attr.removesuffix('_ids'))
                for attr in form.special_fields
            }
        )
    layout = EditTranslatorLayout(self, request)
    layout.edit_mode = True

    if not self.coordinates:
        request.warning(
            _('Translator is lacking location and address.')
        )

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': layout.title
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='form.pt',
    name='edit-restricted',
    form=EditorTranslatorForm,
    permission=Private
)
def edit_translator_as_editor(
    self: Translator,
    request: TranslatorAppRequest,
    form: EditorTranslatorForm
) -> RenderData | BaseResponse:

    if request.is_admin:
        return request.redirect(request.link(self, name='edit'))

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))
    if not form.errors:
        form.process(obj=self)
    layout = EditTranslatorLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': layout.title
    }


@TranslatorDirectoryApp.view(
    model=Translator,
    request_method='DELETE',
    permission=Secret
)
def delete_translator(
    self: Translator,
    request: TranslatorAppRequest
) -> None:

    request.assert_valid_csrf_token()
    TranslatorCollection(request.app).delete(self)
    request.success(_('Translator successfully deleted'))


@TranslatorDirectoryApp.form(
    model=Translator,
    name='report-change',
    template='form.pt',
    permission=Personal,
    form=TranslatorMutationForm
)
def report_translator_change(
    self: Translator,
    request: TranslatorAppRequest,
    form: TranslatorMutationForm
) -> RenderData | BaseResponse:

    if request.is_member:
        raise HTTPForbidden()

    if form.submitted(request):
        assert request.current_username is not None
        session = request.session

        # Get uploaded files from the form
        uploaded_files = form.get_files()
        file_ids: list[str] = []
        if uploaded_files:
            self.files.extend(uploaded_files)
            session.flush()
            file_ids = [f.id for f in uploaded_files]

        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='TRN',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': request.current_username,
                    'submitter_message': form.submitter_message.data,
                    'proposed_changes': form.proposed_changes,
                    'file_ids': file_ids,
                },
            )
            TicketMessage.create(ticket, request, 'opened', 'external')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_('Your ticket has been opened'),
            receivers=(request.current_username, ),
            ticket=ticket,
            send_self=True
        )
        for email in emails_for_new_ticket(request, ticket):
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened_info.pt',
                subject=_('New ticket'),
                ticket=ticket,
                receivers=(email, ),
                content={'model': ticket},
            )

        request.app.send_websocket(
            channel=request.app.websockets_private_channel,
            message={
                'event': 'browser-notification',
                'title': request.translate(_('New ticket')),
                'created': ticket.created.isoformat()
            },
            groupids=request.app.groupids_for_ticket(ticket),
        )

        request.success(_('Thank you for your submission!'))
        return redirect(request.link(ticket, 'status'))

    layout = ReportTranslatorChangesLayout(self, request)

    return {
        'layout': layout,
        'title': layout.title,
        'form': form
    }


@TranslatorDirectoryApp.view(
    model=Translator,
    name='confirm-current-data',
    permission=Personal,
)
def confirm_current_data(
    self: Translator,
    request: TranslatorAppRequest
) -> BaseResponse:

    TranslatorCollection(request.app).confirm_current_data(self)
    request.success(_('Your data has been confirmed'))
    return redirect(request.link(self))


@TranslatorDirectoryApp.form(
    model=Translator,
    template='form.pt',
    name='add-time-report',
    form=TranslatorTimeReportForm,
    permission=Personal,
)
def add_time_report(
    self: Translator,
    request: TranslatorAppRequest,
    form: TranslatorTimeReportForm,
) -> RenderData | BaseResponse:

    if form.submitted(request):

        session = request.session
        current_user = request.current_user

        duration_hours = form.get_duration_hours()
        duration_minutes = int(float(duration_hours) * 60)

        hourly_rate = form.get_hourly_rate(self)
        surcharge_types = form.get_surcharge_types()
        travel_comp, travel_distance = form.calculate_travel_details(
            self, request
        )

        start_dt, end_dt = form.get_datetime_range()
        start_dt = replace_timezone(start_dt, 'Europe/Zurich')
        end_dt = replace_timezone(end_dt, 'Europe/Zurich')

        # Calculate break time in minutes
        break_minutes = 0
        if form.break_time.data:
            break_minutes = (
                form.break_time.data.hour * 60 + form.break_time.data.minute
            )

        # Calculate night hours (in minutes)
        night_hours = form.calculate_night_hours()
        night_minutes = int(float(night_hours) * 60)

        # Calculate weekend/holiday hours
        weekend_holiday_hours = form.calculate_weekend_holiday_hours()
        weekend_holiday_minutes = int(float(weekend_holiday_hours) * 60)

        try:
            accountant_emails = set(
                get_accountant_emails_for_finanzstelle(
                    request, form.finanzstelle.data
                )
            )
        except ValueError as e:
            request.warning(str(e))
            return redirect(request.link(self))

        # Create report with all fields except total_compensation
        assert form.assignment_type.data is not None

        if form.assignment_type.data == 'on-site':
            location = (
                form.assignment_location_override.data
                or form.assignment_location.data
            )
        else:
            location = None

        report = TranslatorTimeReport(
            translator=self,
            created_by=current_user,
            assignment_type=form.assignment_type.data,
            assignment_location=location,
            finanzstelle=form.finanzstelle.data,
            duration=duration_minutes,
            break_time=break_minutes,
            night_minutes=night_minutes,
            weekend_holiday_minutes=weekend_holiday_minutes,
            case_number=form.case_number.data or None,
            assignment_date=start_dt.date(),
            start=start_dt,
            end=end_dt,
            hourly_rate=hourly_rate,
            surcharge_types=surcharge_types if surcharge_types else None,
            travel_compensation=travel_comp,
            travel_distance=travel_distance,
            # Temporary, will be calculated next
            total_compensation=Decimal('0'),
            notes=form.notes.data or None,
        )

        # Use centralized calculation from model
        breakdown = report.calculate_compensation_breakdown()
        report.total_compensation = breakdown['total']
        session.add(report)
        session.flush()

        assert request.current_username is not None

        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='TRP',
                handler_id=uuid4().hex,
                handler_data={
                    'translator_id': str(self.id),
                    'submitter_email': request.current_username,
                    'time_report_id': str(report.id),
                },
            )
            TicketMessage.create(ticket, request, 'opened', 'external')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_('Your ticket has been opened'),
            receivers=(request.current_username,),
            ticket=ticket,
            send_self=True,
        )

        if self.email:
            send_ticket_mail(
                request=request,
                template='mail_time_report_created_for_translator.pt',
                subject=_('A time report has been submitted for you'),
                receivers=(self.email,),
                ticket=ticket,
                content={
                    'model': ticket,
                    'translator': self,
                    'time_report': report,
                    'accountant_emails': list(accountant_emails),
                },
            )

        for email in emails_for_new_ticket(request, ticket):
            if email in accountant_emails:
                send_ticket_mail(
                    request=request,
                    template='mail_ticket_opened_info.pt',
                    subject=_('New ticket'),
                    ticket=ticket,
                    receivers=(email,),
                    content={'model': ticket},
                )
        for accountant_email in accountant_emails:
            send_ticket_mail(
                request=request,
                template='mail_time_report_created_for_accountant.pt',
                subject=_('New time report for review'),
                ticket=ticket,
                receivers=(accountant_email,),
                content={
                    'model': ticket,
                    'translator': self,
                    'time_report': report,
                },
            )

        request.app.send_websocket(
            channel=request.app.websockets_private_channel,
            message={
                'event': 'browser-notification',
                'title': request.translate(_('New ticket')),
                'created': ticket.created.isoformat(),
            },
            groupids=request.app.groupids_for_ticket(ticket),
        )

        request.success(_('Time report submitted for review'))
        return redirect(request.link(ticket, 'status'))

    layout = TranslatorLayout(self, request)

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': _('Add Time Report'),
        'button_text': request.translate(_('Submit Time Report')),
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='mail_templates.pt',
    name='mail-templates',
    form=MailTemplatesForm,
    permission=Personal
)
def view_mail_templates(
    self: Translator,
    request: TranslatorAppRequest,
    form: MailTemplatesForm
) -> RenderData | BaseResponse:

    layout = MailTemplatesLayout(self, request)
    if form.submitted(request):
        template_name = form.templates.data

        if template_name not in request.app.mail_templates:
            request.alert(_('This file does not seem to exist.'))
            return redirect(request.link(self))

        user = request.current_user
        assert user is not None
        if not user.realname:
            request.alert(
                request.translate(
                    _(
                        'Unfortunately, this account (${account}) does not '
                        'have real name defined, which is required for mail '
                        'templates',
                        mapping={'account': user.username},
                    )
                )
            )
            return redirect(request.link(self))

        signature_file = signature_for_mail_templates(request)
        if not signature_file:
            request.alert(_('Did not find a signature in /files.'))
            return redirect(request.link(self))

        signature_file_name = parse_from_filename(signature_file.name)
        first_name, last_name = user.realname.split(' ')
        additional_fields = {
            'current_date': layout.format_date(utcnow(), 'date'),
            'translator_date_of_birth': layout.format_date(
                self.date_of_birth, 'date'),
            'translator_date_of_decision': layout.format_date(
                self.date_of_decision, 'date'
            ),
            'translator_gender': (
                request.translate(GENDER_MAP[self.gender])
                if self.gender else ''
            ),
            'translator_admission': request.translate(_(self.admission)) or '',
            'sender_first_name': first_name,
            'sender_last_name': last_name,
            'sender_full_name': signature_file_name.sender_full_name,
            'sender_function': signature_file_name.sender_function,
            'sender_abbrev': signature_file_name.sender_abbrev,
            'translator_hometown': self.hometown if self.hometown else '',
            'translator_ticket_number': get_ticket_nr_of_translator(
                self, request
            ),
        }

        docx_template_id = (
            GeneralFileCollection(request.session)
            .query()
            .filter(File.name == template_name)
            .with_entities(File.id)
            .scalar()
        )
        docx_f = get_file(request.app, docx_template_id)
        assert docx_f is not None
        template = docx_f.reference.file.read()
        signature_f = get_file(request.app, signature_file.id)
        assert signature_f is not None
        signature_bytes = signature_f.reference.file.read()

        try:
            __, docx = fill_docx_with_variables(
                BytesIO(template), self, request, BytesIO(signature_bytes),
                **additional_fields
            )
            return Response(
                docx,
                content_type='application/vnd.ms-office',
                content_disposition=f'inline; filename={template_name}',
            )
        except UnrecognizedImageError:
            request.alert(_('The image for the signature could not be '
                          'recognized.'))

    return {
        'layout': layout,
        'model': self,
        'form': form,
        'title': _('Mail templates'),
        'button_text': _('Download'),
    }

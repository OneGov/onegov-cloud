from datetime import datetime
from io import BytesIO
from onegov.file import File
from morepath import redirect
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
from onegov.ticket import TicketCollection, Ticket
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS,\
    INTERPRETING_TYPES, ADMISSIONS, GENDERS, GENDER_MAP
from onegov.translator_directory.forms.mutation import TranslatorMutationForm
from onegov.translator_directory.forms.translator import TranslatorForm,\
    TranslatorSearchForm, EditorTranslatorForm, MailTemplatesForm
from onegov.translator_directory.generate_docx import (
    fill_docx_with_variables, signature_for_mail_templates,
    parse_from_filename)
from onegov.translator_directory.layout import AddTranslatorLayout,\
    TranslatorCollectionLayout, TranslatorLayout, EditTranslatorLayout,\
    ReportTranslatorChangesLayout, MailTemplatesLayout
from onegov.translator_directory.models.translator import Translator
from uuid import uuid4
from xlsxwriter import Workbook
from docx.image.exceptions import UnrecognizedImageError  # type: ignore


@TranslatorDirectoryApp.form(
    model=TranslatorCollection,
    template='form.pt',
    name='new',
    form=TranslatorForm,
    permission=Secret
)
def add_new_translator(self, request, form):

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
def view_translators(self, request, form):
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
def export_translator_directory(self, request):
    output = BytesIO()
    workbook = Workbook(output)

    def format_date(dt):
        if not dt:
            return ''
        return dt.strftime('%Y-%m-%d')

    def format_iterable(listlike):
        return "|".join(listlike) if listlike else ''

    def format_languages(langs):
        return format_iterable((la.name for la in langs))

    def format_guilds(guilds):
        return format_iterable(
            (
                request.translate(PROFESSIONAL_GUILDS[s])
                if s in PROFESSIONAL_GUILDS else s
                for s in guilds
            )
        )

    def format_interpreting_types(types):
        return format_iterable(
            (request.translate(INTERPRETING_TYPES[t]) for t in types)
        )

    def format_admission(admission):
        if not admission:
            return ''
        return request.translate(ADMISSIONS[admission])

    def format_gender(gender):
        if not gender:
            return ''
        return request.translate(GENDERS[gender])

    worksheet = workbook.add_worksheet()
    worksheet.name = request.translate(_("Translator directory"))
    worksheet.write_row(0, 0, (
        request.translate(_("Personal ID")),
        request.translate(_("Admission")),
        request.translate(_("Withholding tax")),
        request.translate(_("Self-employed")),
        request.translate(_("Last name")),
        request.translate(_("First name")),
        request.translate(_("Gender")),
        request.translate(_("Date of birth")),
        request.translate(_("Nationality")),
        request.translate(_("Location")),
        request.translate(_("Address")),
        request.translate(_("Zip Code")),
        request.translate(_("City")),
        request.translate(_("Drive distance")),
        request.translate(_("Swiss social security number")),
        request.translate(_("Bank name")),
        request.translate(_("Bank address")),
        request.translate(_("Account owner")),
        request.translate(_("IBAN")),
        request.translate(_("Email")),
        request.translate(_("Private Phone Number")),
        request.translate(_("Mobile Phone Number")),
        request.translate(_("Office Phone Number")),
        request.translate(_("Availability")),
        request.translate(_("Comments on possible field of application")),
        request.translate(_("Name reveal confirmation")),
        request.translate(_("Date of application")),
        request.translate(_("Date of decision")),
        request.translate(_("Mother tongues")),
        request.translate(_("Spoken languages")),
        request.translate(_("Written languages")),
        request.translate(_("Monitoring languages")),
        request.translate(_("Learned profession")),
        request.translate(_("Current professional activity")),
        request.translate(_("Expertise by professional guild")),
        request.translate(_("Expertise by interpreting type")),
        request.translate(_("Proof of preconditions")),
        request.translate(_("Agency references")),
        request.translate(_("Education as interpreter")),
        request.translate(_("Certificates")),
        request.translate(_("Comments")),
        request.translate(_("Hidden")),
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
            trs.nationality or '',
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
        request.translate(_("Translator directory")).lower(),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response


@TranslatorDirectoryApp.html(
    model=Translator,
    template='translator.pt',
    permission=Personal
)
def view_translator(self, request):
    layout = TranslatorLayout(self, request)
    translator_handler_data = (
        TicketCollection(request.session).by_handler_data_id(self.id)
    )
    hometown_query = translator_handler_data.with_entities(
        Ticket.handler_data['handler_data']['hometown']
    )
    hometown = hometown_query.first()[0] if hometown_query.first() else None

    return {
        'layout': layout,
        'model': self,
        'title': self.title,
        'hometown': hometown
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='form.pt',
    name='edit',
    form=TranslatorForm,
    permission=Secret
)
def edit_translator(self, request, form):

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))
    if not form.errors:
        form.process(
            obj=self,
            **{attr: form.get_ids(self, attr.split('_ids')[0])
                for attr in form.special_fields}
        )
    layout = EditTranslatorLayout(self, request)

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
def edit_translator_as_editor(self, request, form):

    if request.is_admin:
        return request.redirect(request.link(self, name='edit'))

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Your changes were saved"))
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
def delete_translator(self, request):

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
def report_translator_change(self, request, form):
    if form.submitted(request):
        session = request.session
        with session.no_autoflush:
            ticket = TicketCollection(session).open_ticket(
                handler_code='TRN',
                handler_id=uuid4().hex,
                handler_data={
                    'id': str(self.id),
                    'submitter_email': request.current_username,
                    'submitter_message': form.submitter_message.data,
                    'proposed_changes': form.proposed_changes
                }
            )
            TicketMessage.create(ticket, request, 'opened')
            ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_ticket_opened.pt',
            subject=_("Your ticket has been opened"),
            receivers=(request.current_username, ),
            ticket=ticket,
            send_self=True
        )
        if request.email_for_new_tickets:
            send_ticket_mail(
                request=request,
                template='mail_ticket_opened_info.pt',
                subject=_("New ticket"),
                ticket=ticket,
                receivers=(request.email_for_new_tickets, ),
                content={
                    'model': ticket
                }
            )

        request.app.send_websocket(
            channel=request.app.websockets_private_channel,
            message={
                'event': 'browser-notification',
                'title': request.translate(_('New ticket')),
                'created': ticket.created.isoformat()
            }
        )

        request.success(_("Thank you for your submission!"))
        return redirect(request.link(ticket, 'status'))

    layout = ReportTranslatorChangesLayout(self, request)

    return {
        'layout': layout,
        'title': layout.title,
        'form': form
    }


@TranslatorDirectoryApp.form(
    model=Translator,
    template='mail_templates.pt',
    name='mail-templates',
    form=MailTemplatesForm,
    permission=Personal
)
def view_mail_templates(self, request, form):

    layout = MailTemplatesLayout(self, request)
    if form.submitted(request):
        template_name = form.templates.data

        if template_name not in request.app.mail_templates:
            request.alert(_('This file does not seem to exist.'))
            return redirect(request.link(self))

        user = request.current_user
        if not getattr(user, 'realname', None):
            request.alert(_('Unfortunately, this account does not have real '
                            'name defined, which is required for mail '
                            'templates'))
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
            'translator_gender': request.translate(GENDER_MAP.get(
                self.gender)),
            'translator_admission': request.translate(_(self.admission)) or '',
            'sender_first_name': first_name,
            'sender_last_name': last_name,
            'sender_full_name': signature_file_name.sender_full_name,
            'sender_function': signature_file_name.sender_function,
            'sender_abbrev': signature_file_name.sender_abbrev,
        }

        docx_template_id = (
            GeneralFileCollection(request.session)
            .query()
            .filter(File.name == template_name)
            .with_entities(File.id)
            .first()
        )
        docx_f = get_file(request.app, docx_template_id)
        template = docx_f.reference.file.read()
        signature_f = get_file(request.app, signature_file.id)
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

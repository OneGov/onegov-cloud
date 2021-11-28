from datetime import datetime
from io import BytesIO

from webob.exc import HTTPNotFound
from xlsxwriter import Workbook

from onegov.org.models import Organisation
from onegov.translator_directory import _
from onegov.core.security import Secret, Personal, Private
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS, \
    INTERPRETING_TYPES, ADMISSIONS, GENDERS
from onegov.translator_directory.forms.translator import TranslatorForm, \
    TranslatorSearchForm, EditorTranslatorForm
from onegov.translator_directory.layout import AddTranslatorLayout, \
    TranslatorCollectionLayout, TranslatorLayout, EditTranslatorLayout
from onegov.translator_directory.models.translator import Translator
from morepath.request import Response
from onegov.core.custom import json


@TranslatorDirectoryApp.form(
    model=TranslatorCollection,
    template='form.pt',
    name='new',
    form=TranslatorForm,
    permission=Secret
)
def add_new_translator(self, request, form):

    if form.submitted(request):
        translator = self.add(**form.get_useful_data())
        request.success(_('Added a new translator'))
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
    return {
        'layout': layout,
        'model': self,
        'title': self.title
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
def delete_course_event(self, request):

    request.assert_valid_csrf_token()
    TranslatorCollection(request.session).delete(self)
    request.success(_('Translator successfully deleted'))


@TranslatorDirectoryApp.view(
    model=Organisation,
    permission=Personal,
    name='voucher'
)
def get_static_excel_file(self, request):
    file = request.app.voucher_excel_file
    if not file:
        return HTTPNotFound()

    return Response(
        file.read(),
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition=f'inline; filename={file.filename}'
    )

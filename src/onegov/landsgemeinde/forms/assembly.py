from datetime import date
from onegov.landsgemeinde import _
# from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.form import Form
# from onegov.form.fields import UploadField
# from onegov.form.validators import FileSizeLimit
# from onegov.form.validators import WhitelistedMimeType
# from onegov.quill import QuillField
# from wtforms.fields import BooleanField
from wtforms.fields import DateField
# from wtforms.fields import IntegerField
# from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
# from wtforms.validators import Optional
# from wtforms.validators import ValidationError
from onegov.org.forms.fields import HtmlField
from onegov.landsgemeinde.layouts import DefaultLayout


class AssemblyForm(Form):

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    # todo:
    # explanations_pdf = UploadField(
    #     label=_("Memorial (PDF)"),
    #     validators=[
    #         WhitelistedMimeType({'application/pdf'}),
    #         FileSizeLimit(100 * 1024 * 1024)
    #     ]
    # )
    #
    # protocol_pdf = UploadField(
    #     label=_("Protocol (PDF)"),
    #     validators=[
    #         WhitelistedMimeType({'application/pdf'}),
    #         FileSizeLimit(100 * 1024 * 1024)
    #     ]
    # )
    #
    # audio_mp3 = UploadField(
    #     label=_("Audio (MP3)"),
    #     validators=[
    #         WhitelistedMimeType({'audio/mpeg'}),
    #         FileSizeLimit(600 * 1024 * 1024)
    #     ]
    # )

    overview = HtmlField(
        label=_("Text")
    )

    # todo: validate unique date

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')

    def update_model(self, model):
        # model.last_result_change = model.timestamp()
        model.date = self.date.data
        # model.domain = self.request.app.principal.domain
        # model.id = model.id_from_title(
        #     "{} {}".format(
        #         self.request.translate(_("Assembly")),
        #         self.date.data.year
        #     ),
        #     self.request.session
        # )
        # model.title_translations = {
        #     locale: self.get_title(locale)
        #     for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH')
        # }
        # if model.content is None:
        #     model.content = {}
        # model.content['overview'] = self.overview.data
        #
        # action = getattr(self.explanations_pdf, 'action', '')
        # if action == 'delete':
        #     del model.explanations_pdf
        # if action == 'replace' and self.explanations_pdf.data:
        #     model.explanations_pdf = (
        #         self.explanations_pdf.file,
        #         self.explanations_pdf.filename,
        #     )
        #
        # action = getattr(self.protocol_pdf, 'action', '')
        # if action == 'delete':
        #     del model.protocol_pdf
        # if action == 'replace' and self.protocol_pdf.data:
        #     model.protocol_pdf = (
        #         self.protocol_pdf.file,
        #         self.protocol_pdf.filename,
        #     )
        #
        # action = getattr(self.audio_mp3, 'action', '')
        # if action == 'delete':
        #     del model.audio_mp3
        # if action == 'replace' and self.audio_mp3.data:
        #     model.audio_mp3 = (
        #         self.audio_mp3.file,
        #         self.audio_mp3.filename,
        #     )

    def apply_model(self, model):
        self.date.data = model.date
        # self.overview.data = (model.content or {}).get('overview')
        #
        # file = model.explanations_pdf
        # if file:
        #     self.explanations_pdf.data = {
        #         'filename': file.reference.filename,
        #         'size': file.reference.file.content_length,
        #         'mimetype': file.reference.content_type
        #     }
        #
        # file = model.protocol_pdf
        # if file:
        #     self.protocol_pdf.data = {
        #         'filename': file.reference.filename,
        #         'size': file.reference.file.content_length,
        #         'mimetype': file.reference.content_type
        #     }
        #
        # file = model.audio_mp3
        # if file:
        #     self.audio_mp3.data = {
        #         'filename': file.reference.filename,
        #         'size': file.reference.file.content_length,
        #         'mimetype': file.reference.content_type
        #     }

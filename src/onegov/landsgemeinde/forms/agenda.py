# from datetime import date
# from onegov.ballot import AssemblyAgendaItem
from onegov.election_day import _
# from onegov.election_day.layouts import DefaultLayout
from onegov.form import Form
from onegov.form.fields import TimeField
# from onegov.form.fields import UploadField
# from onegov.form.validators import FileSizeLimit
# from onegov.form.validators import WhitelistedMimeType
# from onegov.quill import QuillField
from wtforms.fields import BooleanField
# from wtforms.fields import DateField
from wtforms.fields import IntegerField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
# from wtforms.validators import ValidationError
from onegov.org.forms.fields import HtmlField
from onegov.landsgemeinde.layouts import DefaultLayout


class AgendaItemForm(Form):

    number = IntegerField(
        label=_("Number"),
        validators=[
            InputRequired()
        ],
    )

    title = TextAreaField(
        label=_("Title"),
        render_kw={'rows': 5}
    )

    irrelevant = BooleanField(
        label=_("Irrelevant"),
    )

    start = TimeField(
        label=_("Start time"),
        validators=[
            Optional()
        ],
    )

    scheduled = BooleanField(
        label=_("Scheduled"),
    )

    counted = BooleanField(
        label=_("Completed"),
    )

    # todo:
    # explanations_pdf = UploadField(
    #     label=_("Extract from the memorial (PDF)"),
    #     fieldset=_("Overview"),
    #     validators=[
    #         WhitelistedMimeType({'application/pdf'}),
    #         FileSizeLimit(100 * 1024 * 1024)
    #     ],
    # )

    overview = HtmlField(
        label=_("Overview"),
    )

    text = HtmlField(
        label=_("Content"),
    )

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')

    def get_useful_data(self):
        data = super().get_useful_data()
        data['assembly_id'] = self.model.assembly.id
        return data

    # todo:
    # def validate_number(self, field):
    #     if field.data:
    #         query = self.request.session.query(AssemblyAgendaItem)
    #         query = query.filter(
    #             AssemblyAgendaItem.assembly_id == self.assembly.id,
    #             AssemblyAgendaItem.number == field.data
    #         )
    #         if isinstance(self.model, AssemblyAgendaItem):
    #             query = query.filter(AssemblyAgendaItem.id != self.model.id)
    #         if query.first():
    #             raise ValidationError(_("Number already used."))

    # def update_model(self, model):
    #     model.last_result_change = model.timestamp()
    #     model.counted = self.counted.data
    #     model.irrelevant = self.irrelevant.data
    #     model.number = self.number.data
    #     model.title = self.title.data
    #     model.start = self.start.data
    #     model.scheduled = self.scheduled.data
    #     if model.content is None:
    #         model.content = {}
    #     model.content['overview'] = self.overview.data
    #     model.content['content'] = self.content.data
    #
    #     action = getattr(self.explanations_pdf, 'action', '')
    #     if action == 'delete':
    #         del model.explanations_pdf
    #     if action == 'replace' and self.explanations_pdf.data:
    #         model.explanations_pdf = (
    #             self.explanations_pdf.file,
    #             self.explanations_pdf.filename,
    #         )

    # def apply_model(self, model):
    #     self.counted.data = model.counted
    #     self.irrelevant.data = model.irrelevant
    #     self.number.data = model.number
    #     self.title.data = model.title
    #     self.start.data = model.start
    #     self.scheduled.data = model.scheduled
    #     self.overview.data = (model.content or {}).get('overview')
    #     self.content.data = (model.content or {}).get('content')
    #
    #     file = model.explanations_pdf
    #     if file:
    #         self.explanations_pdf.data = {
    #             'filename': file.reference.filename,
    #             'size': file.reference.file.content_length,
    #             'mimetype': file.reference.content_type
    #         }

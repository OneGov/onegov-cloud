from onegov.election_day import _
from onegov.form.fields import TagsField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde.forms.file import NamedFileForm
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.org.forms.fields import HtmlField
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


class AgendaItemForm(NamedFileForm):

    number = IntegerField(
        label=_('Number'),
        fieldset=_('General'),
        validators=[
            InputRequired()
        ],
    )

    title = TextAreaField(
        label=_('Title'),
        fieldset=_('General'),
        render_kw={'rows': 5}
    )

    memorial_pdf = UploadField(
        label=_('Memorial (PDF)'),
        fieldset=_('General'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    irrelevant = BooleanField(
        label=_('Irrelevant'),
        fieldset=_('General'),
    )

    start = TimeField(
        label=_('Start time'),
        fieldset=_('Progress'),
        validators=[
            Optional()
        ],
    )

    scheduled = BooleanField(
        label=_('Scheduled'),
        fieldset=_('Progress'),
    )

    counted = BooleanField(
        label=_('Completed'),
        fieldset=_('Progress'),
    )

    overview = HtmlField(
        label=_('Text'),
        fieldset=_('Overview'),
    )

    text = HtmlField(
        label=_('Text'),
        fieldset=_('Content'),
    )

    resolution = HtmlField(
        label=_('Text'),
        fieldset=_('Resolution'),
    )

    # todo: provide defaults
    resolution_tags = TagsField(
        label=_('Tags'),
        fieldset=_('Resolution')
    )

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.request.include('tags-input')

    def get_useful_data(self):
        data = super().get_useful_data()
        data['assembly_id'] = self.model.assembly.id
        return data

    def validate_number(self, field):
        if field.data:
            query = self.request.session.query(AgendaItem)
            query = query.filter(
                AgendaItem.assembly_id == self.model.assembly.id,
                AgendaItem.number == field.data
            )
            if isinstance(self.model, AgendaItem):
                query = query.filter(AgendaItem.id != self.model.id)
            if query.first():
                raise ValidationError(_('Number already used.'))

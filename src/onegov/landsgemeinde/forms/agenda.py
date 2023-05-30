from onegov.election_day import _
from onegov.form.fields import TagsField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models.agenda import STATES
from onegov.org.forms.fields import HtmlField
from sqlalchemy import desc
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


class AgendaItemForm(NamedFileForm):

    number = IntegerField(
        label=_('Number'),
        fieldset=_('General'),
    )

    state = RadioField(
        _('State'),
        fieldset=_('General'),
        choices=list(STATES.items()),
        validators=[
            InputRequired()
        ],
        default=list(STATES.keys())[0]
    )

    title = TextAreaField(
        label=_('Title'),
        fieldset=_('General'),
        render_kw={'rows': 5}
    )

    irrelevant = BooleanField(
        label=_('Irrelevant'),
        fieldset=_('General'),
    )

    memorial_pdf = UploadField(
        label=_('Excerpt from the Memorial (PDF)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    start = TimeField(
        label=_('Start time'),
        fieldset=_('Progress'),
        validators=[
            Optional()
        ],
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

    tacitly_accepted = BooleanField(
        label=_('Tacitly accepted'),
        fieldset=_('Resolution'),
    )

    # todo: provide defaults
    resolution_tags = TagsField(
        label=_('Tags'),
        fieldset=_('Resolution')
    )

    @property
    def next_number(self):
        query = self.request.session.query(AgendaItem.number)
        query = query.filter(AgendaItem.assembly_id == self.model.assembly.id)
        query = query.order_by(desc(AgendaItem.number))
        query = query.limit(1)
        return (query.scalar() or 0) + 1

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

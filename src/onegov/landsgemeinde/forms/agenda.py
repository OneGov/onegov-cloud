from datetime import date, datetime
from onegov.election_day import _
from onegov.form.fields import PanelField, TagsField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models.agenda import STATES
from onegov.landsgemeinde.utils import timestamp_to_seconds
from onegov.landsgemeinde.utils import seconds_to_timestamp
from onegov.org.forms.fields import HtmlField
from sqlalchemy import func
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import NumberRange
from wtforms.validators import ValidationError


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.request import LandsgemeindeRequest


class AgendaItemForm(NamedFileForm):

    request: 'LandsgemeindeRequest'

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
        fieldset=_('Memorial'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    memorial_page = IntegerField(
        description=_(
            "Links to the whole memorial (if there is one linked to the "
            "assembly), but opens it on the chosen page number"
        ),
        label=_('Alternatively: Page from the Memorial'),
        fieldset=_('Memorial'),
        validators=[
            NumberRange(min=1),
            Optional()
        ],
    )

    timestamp_info = PanelField(
        text=_('If the start field is filled and the video timestamp field is '
               'left empty, a timestamp is automatically calculated based on '
               'the start time of the agenda item in relation to the start '
               'time of the live broadcast.'),
        fieldset=_('Progress'),
        kind='info'
    )

    start_time = TimeField(
        label=_('Start'),
        fieldset=_('Progress'),
        render_kw={
            'long_description': _(
                'Automatically updated when agenda item changed to ongoing.'
            ),
            'step': 1},
        format='%H:%M:%S',  # specify the format to include seconds
        validators=[
            Optional()
        ],
    )

    video_timestamp = StringField(
        label=_('Video timestamp'),
        fieldset=_('Progress'),
        description='1h2m1s',
        validators=[
            Optional()
        ],
    )

    calculated_timestamp = PanelField(
        text='',
        fieldset=_('Progress'),
        kind='warning'
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
    def next_number(self) -> int:
        query = self.request.session.query(func.max(AgendaItem.number))
        query = query.filter(AgendaItem.assembly_id == self.model.assembly.id)
        return (query.scalar() or 0) + 1

    def on_request(self) -> None:
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')
        self.request.include('tags-input')

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data(exclude=('calculated_timestamp',
                                                'timestamp_info'))
        data['assembly_id'] = self.model.assembly.id
        return data

    def validate_number(self, field: IntegerField) -> None:
        if field.data:
            session = self.request.session
            query = session.query(AgendaItem)
            query = query.filter(
                AgendaItem.assembly_id == self.model.assembly.id,
                AgendaItem.number == field.data
            )
            if isinstance(self.model, AgendaItem):
                query = query.filter(AgendaItem.id != self.model.id)
            if session.query(query.exists()).scalar():
                raise ValidationError(_('Number already used.'))

    def validate_video_timestamp(self, field: StringField) -> None:
        if field.data and timestamp_to_seconds(field.data) is None:
            raise ValidationError(_('Invalid timestamp.'))

    def process_obj(self, obj: AgendaItem) -> None:  # type:ignore[override]
        super().process_obj(obj)
        if (obj.calculated_timestamp):
            self.calculated_timestamp.text = (self.request.translate(_(
                'Automatically calculated timestamp: '))
                + str(obj.calculated_timestamp))
        else:
            self.delete_field('calculated_timestamp')

    def populate_obj(self, obj: AgendaItem) -> None:  # type:ignore[override]
        super().populate_obj(obj, exclude=("timestamp_info",))
        if self.start_time.data and obj.assembly.start_time:
            seconds = (datetime.combine(
                date.today(), self.start_time.data) - datetime.combine(
                    date.today(), obj.assembly.start_time)
            ).seconds
            obj.calculated_timestamp = seconds_to_timestamp(seconds)

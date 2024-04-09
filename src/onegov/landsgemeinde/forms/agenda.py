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
        text=_('Wird das Start-Feld gefüllt und das Video-Zeitstempel-Feld '
               'leer gelassen wird automatisch ein Zeitstempel anhand '
               'der Startzeit des Traktandums in Relation zur Startzeit der '
               'Live-Übertragung berechnet.'),
        fieldset=_('Progress'),
        kind='info'
    )

    start_time = TimeField(
        label=_('Start'),
        fieldset=_('Progress'),
        render_kw={'long_description': _(
            'Automatically updated when agenda item changed to ongoing.'
        )},
        validators=[
            Optional()
        ],
    )

    video_timestamp = StringField(
        label=_('Video timestamp'),
        fieldset=_('Progress'),
        description='2m1s',
        validators=[
            Optional()
        ],
    )


    calculated_timestamp = PanelField(
        text=_('Automatisch berechneter Zeitstempel: 1h2m3s '),
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
        data = super().get_useful_data()
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

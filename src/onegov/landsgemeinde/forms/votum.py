from onegov.election_day import _
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import Votum
from onegov.org.forms.fields import HtmlField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError
from onegov.landsgemeinde.models.votum import STATES


class VotumForm(NamedFileForm):

    number = IntegerField(
        label=_('Number'),
        fieldset=_('General'),
        validators=[
            InputRequired()
        ],
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

    person_name = StringField(
        label=_('Name'),
        fieldset=_('Person'),
        render_kw={'rows': 5}
    )

    person_function = StringField(
        label=_('Function'),
        fieldset=_('Person'),
        render_kw={'rows': 5}
    )

    person_place = StringField(
        label=_('Place'),
        fieldset=_('Person'),
        render_kw={'rows': 5}
    )

    person_political_affiliation = StringField(
        label=_('Party or parliamentary group'),
        fieldset=_('Person'),
        render_kw={'rows': 5}
    )

    person_picture = UploadField(
        label=_('Picture'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({
                'image/jpeg',
                'image/png',
            }),
            FileSizeLimit(1 * 1024 * 1024)
        ]
    )

    start = TimeField(
        label=_('Start time'),
        fieldset=_('Progress'),
        validators=[
            Optional()
        ],
    )

    motion = HtmlField(
        label=_('Text'),
        fieldset=_('Motion'),
    )

    statement_of_reasons = HtmlField(
        label=_('Text'),
        fieldset=_('Statement of reasons'),
    )

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')

    def get_useful_data(self):
        data = super().get_useful_data()
        data['agenda_item_id'] = self.model.agenda_item.id
        return data

    def validate_number(self, field):
        if field.data:
            query = self.request.session.query(Votum)
            query = query.filter(
                Votum.agenda_item_id == self.model.agenda_item.id,
                Votum.number == field.data
            )
            if isinstance(self.model, Votum):
                query = query.filter(Votum.id != self.model.id)
            if query.first():
                raise ValidationError(_('Number already used.'))

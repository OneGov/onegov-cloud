from onegov.election_day import _
from onegov.election_day.models.data_source import UPLOAD_TYPE_LABELS
from onegov.form import Form
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import InputRequired


class DataSourceForm(Form):

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ],
    )

    upload_type = RadioField(
        _("Type"),
        choices=list(UPLOAD_TYPE_LABELS),
        validators=[
            InputRequired()
        ],
        default='vote'
    )

    def update_model(self, model):
        model.name = self.name.data
        model.type = self.upload_type.data

    def apply_model(self, model):
        self.name.data = model.name
        self.upload_type.data = model.type


class DataSourceItemForm(Form):

    item = RadioField(
        label="",
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    district = StringField(
        label="'SortWahlkreis'",
        validators=[
            InputRequired()
        ],
        render_kw=dict(force_simple=True)
    )

    number = StringField(
        label="'SortGeschaeft'",
        validators=[
            InputRequired()
        ],
        render_kw=dict(force_simple=True)
    )

    callout = ''

    def populate(self, source):
        self.type = source.type
        self.item.label.text = dict(UPLOAD_TYPE_LABELS).get(self.type)
        self.item.choices = [
            (item.id, item.title) for item in source.query_candidates()
        ]
        self.callout = ''
        if not self.item.choices:
            if self.type == 'vote':
                self.callout = _("No votes yet.")
            else:
                self.callout = _("No elections yet.")

    def update_model(self, model):
        if self.type == 'vote':
            model.vote_id = self.item.data
        else:
            model.election_id = self.item.data

        model.district = self.district.data
        model.number = self.number.data

    def apply_model(self, model):
        if self.type == 'vote':
            self.item.data = model.vote_id
        else:
            self.item.data = model.election_id

        self.district.data = model.district
        self.number.data = model.number

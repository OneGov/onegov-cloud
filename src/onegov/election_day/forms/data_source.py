from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.models.data_source import UPLOAD_TYPE_LABELS
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest
    from onegov.election_day.models import DataSource
    from onegov.election_day.models import DataSourceItem


class DataSourceForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ],
    )

    upload_type = RadioField(
        _('Type'),
        choices=list(UPLOAD_TYPE_LABELS),
        validators=[
            InputRequired()
        ],
        default='vote'
    )

    def update_model(self, model: DataSource) -> None:
        assert self.name.data is not None
        assert self.upload_type.data is not None
        model.name = self.name.data
        model.type = self.upload_type.data

    def apply_model(self, model: DataSource) -> None:
        self.name.data = model.name
        self.upload_type.data = model.type


class DataSourceItemForm(Form):

    request: ElectionDayRequest

    item = ChosenSelectField(
        label='',
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    number = StringField(
        label="'SortGeschaeft'",
        validators=[
            InputRequired()
        ],
        render_kw={'force_simple': True}
    )

    district = StringField(
        label="'SortWahlkreis'",
        render_kw={'force_simple': True}
    )

    callout = ''

    def populate(self, source: DataSource) -> None:
        layout = DefaultLayout(None, self.request)

        self.type = source.type
        self.item.label.text = dict(UPLOAD_TYPE_LABELS).get(self.type, '')
        self.item.choices = [
            (
                item.id,
                '{} {} {}'.format(
                    layout.format_date(item.date, 'date'),
                    item.shortcode or '',
                    item.title
                ).replace('  ', ' ')
            ) for item in source.query_candidates()
        ]
        self.callout = ''
        if not self.item.choices:
            if self.type == 'vote':
                self.callout = _('No votes yet.')
            else:
                self.callout = _('No elections yet.')

    def update_model(self, model: DataSourceItem) -> None:
        if self.type == 'vote':
            model.vote_id = self.item.data
        else:
            model.election_id = self.item.data

        model.district = self.district.data
        model.number = self.number.data

    def apply_model(self, model: DataSourceItem) -> None:
        if self.type == 'vote':
            self.item.data = model.vote_id
        else:
            self.item.data = model.election_id

        self.district.data = model.district
        self.number.data = model.number

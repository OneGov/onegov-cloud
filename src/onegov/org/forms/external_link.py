from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import URLField
from onegov.org import _
from onegov.org.models.external_link import ExternalLinkCollection
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import URL


class ExternalLinkForm(Form):

    title = StringField(
        label=_('Title'),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes briefly what this entry is about'),
        validators=[],
        render_kw={'rows': 4})

    url = URLField(
        label=_('URL'),
        description=_('Url pointing to another website'),
        validators=[InputRequired(), URL()]
    )

    group = StringField(
        label=_('Group'),
        description=_('Used to group this link in the overview')
    )

    member_of = SelectField(
        label=_('Name of the list view this link will be shown'),
        choices=[]
    )

    def on_request(self) -> None:
        if isinstance(self.model, ExternalLinkCollection):
            self.member_of.choices = [
                (id_, self.request.translate(_(name)))
                for id_, name in self.model.form_choices()
            ]
        else:
            self.delete_field('member_of')

from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.filters import strip_whitespace
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models import Search


class SearchForm(Form):

    model: Search

    type = MultiCheckboxField(
        choices=()
    )

    q = StringField(
        id='search',
        validators=[InputRequired()],
        filters=(strip_whitespace, ),
        render_kw={
            'data-typeahead-subject': True,
            'autocomplete': 'off',
            'autocorrect': 'off',
            'autofocus': True,
        }
    )

    def on_request(self) -> None:
        self.type.choices = self.model.document_type_filter_choices
        if len(self.type.choices) < 2:
            self.delete_field('type')

from __future__ import annotations

from onegov.election_day import _
from onegov.form import Form
from wtforms.fields import BooleanField


class EmptyForm(Form):
    pass


class ClearResultsForm(Form):

    clear_all = BooleanField(
        label=_('Clear everything'),
        description=_(
            'Beware that some formats such as eCH ship candidates, lists and '
            'list connections separately.'
        ),
        render_kw={'force_simple': True},
        default=False
    )

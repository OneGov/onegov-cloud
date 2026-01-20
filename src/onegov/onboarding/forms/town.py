from __future__ import annotations

import re

from onegov.form import Form
from onegov.form.fields import ColorField
from onegov.form.fields import PhoneNumberField
from onegov.onboarding import _
from wtforms.fields import BooleanField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Length


class TownForm(Form):
    """ First step when starting a new town. """

    # the name is limited to 63 characters because it has to fit into a
    # subdomain which may not exceed that length
    name = StringField(
        label=_('Town Name'),
        description=_('The name of your town (real or fictitious)'),
        validators=[InputRequired(), Length(max=63)],
        render_kw={
            'autofocus': '',
            'class_': 'autocomplete',
            'data-source': 'town-names'
        }
    )

    user_name = StringField(
        label=_('Name'),
        description=_('Your Name'),
        validators=[InputRequired()],
    )
    user = EmailField(
        label=_('E-Mail'),
        description=_('Your e-mail address'),
        validators=[InputRequired(), Email()]
    )

    phone_number = PhoneNumberField(
        label=_('Phone number'),
        description='+41791112233',
        validators=[
            InputRequired(),
        ],
        render_kw={
            'autocomplete': 'tel',
        }
    )

    checkbox = BooleanField(
        label=_('I work for a local government and would like to test '
                'admin.digital for my municipality without obligation and '
                'free of charge.'),
        validators=[InputRequired()],
    )

    color = ColorField(
        label=_('Primary Color'),
        validators=[InputRequired()],
        default='#005ba1'
    )

    def ensure_valid_name(self) -> bool:
        name = self.name.data
        assert name is not None
        if not re.match(r'^[A-Za-z\s]+$', name) or not name.strip():
            assert isinstance(self.name.errors, list)
            self.name.errors.append(
                _('Only characters are allowed')
            )
            return False
        return True


class FinishForm(Form):
    pass

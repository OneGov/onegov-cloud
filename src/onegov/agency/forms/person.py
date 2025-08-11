from __future__ import annotations
from wtforms.fields.simple import StringField
from onegov.agency.forms import PersonMutationForm
from onegov.agency import _
from onegov.org.forms import PersonForm


class AgencyPersonForm(PersonForm):

    external_user_id = StringField(_('External ID'))

    staff_number = StringField(label=_('Personnel Number'))


class AuthenticatedPersonMutationForm(PersonMutationForm):
    """ Like PersonMutationForm, but includes fields which shouldn't be
    public.
    """

    external_user_id = StringField(
        fieldset=_('Proposed changes'), label=_('External ID')
    )

    staff_number = StringField(
        fieldset=_('Proposed changes'), label=_('Number')
    )

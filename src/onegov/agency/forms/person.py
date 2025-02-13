from __future__ import annotations
from onegov.agency.forms import PersonMutationForm
from onegov.form.parser.core import StringField
from onegov.agency import _
from onegov.org.forms import PersonForm


class AgencyPersonForm(PersonForm):

    external_user_id = StringField(_('External ID'), required=False)


class AuthenticatedPersonMutationForm(PersonMutationForm):
    """ Like PersonMutationForm, but includes fields which shouldn't be
    public.
    """

    external_user_id = StringField(
        fieldset=_('Proposed changes'), label=_('External ID'), required=False
    )

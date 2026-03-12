from __future__ import annotations

from onegov.form.fields import HoneyPotField
from onegov.user.forms import MTANForm
from onegov.user.forms import RequestMTANForm


class PublicMTANForm(MTANForm):
    """ The base MTAN form extended with a ``HoneyPotField``. """

    duplicate_of = HoneyPotField(
        render_kw={
            'autocomplete': 'lazy-wolves'
        }
    )


class PublicRequestMTANForm(RequestMTANForm):
    """ The base request MTAN form extended with a ``HoneyPotField``. """

    duplicate_of = HoneyPotField(
        render_kw={
            'autocomplete': 'lazy-wolves'
        }
    )

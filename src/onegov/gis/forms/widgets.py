from __future__ import annotations

from wtforms.widgets import TextInput


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup
    from .fields import CoordinatesField


class CoordinatesWidget(TextInput):
    """ Widget holding and showing the data behind the
    :class:`onegov.gis.forms.fields.CoordinatesField` class.

    Basically a textfield that stores json. Meant to be enhanced on the browser
    using javascript.

    """

    def __call__(
        self,
        field: CoordinatesField,  # type:ignore[override]
        **kwargs: Any
    ) -> Markup:

        kwargs['class_'] = (kwargs.get('class_', '') + ' coordinates').strip()
        return super().__call__(field, **kwargs)

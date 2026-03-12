from __future__ import annotations

from bleach.sanitizer import Cleaner
from markupsafe import Markup
from onegov.quill.widgets import QuillInput
from onegov.quill.widgets import TAGS
from wtforms.fields import TextAreaField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from wtforms.form import BaseForm


class QuillField(TextAreaField):
    """ A textfield using the quill editor and with integrated sanitation.

    Allows to specifiy which tags to use in the editor and for sanitation.
    Available tags are: strong, em, ol and ul (p and br tags are always
    possible).

    """

    data: Markup

    def __init__(
        self,
        *,
        tags: Sequence[str] | None = None,
        **kwargs: Any
    ):
        if tags is None:
            tags = TAGS
        else:
            tags = list(set(tags) & set(TAGS))

        super().__init__(**kwargs)

        self.widget = QuillInput(tags=tags)

        tags = ['p', 'br', *tags]
        if 'ol' in tags or 'ul' in tags:
            tags.append('li')

        attributes = {}
        if 'a' in tags:
            attributes['a'] = ['href']

        self.cleaner = Cleaner(tags=tags, attributes=attributes, strip=True)

    def pre_validate(self, form: BaseForm) -> None:
        self.data = Markup(self.cleaner.clean(self.data or ''))  # nosec: B704

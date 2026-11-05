from functools import cached_property
from onegov.agency.models.mutation import Mutation
from onegov.core.html import sanitize_html
from onegov.org.i18n import _
from onegov.page import PageCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models.page import Topic  # ruff: ignore[unused-import]


class TopicMutation(Mutation['Topic', int]):

    @cached_property
    def collection(self) -> PageCollection:  # type: ignore[override]
        return PageCollection(self.session)

    @property
    def labels(self) -> dict[str, str]:
        return {
            'title': _('Title'),
            'lead': _('Lead'),
            'text': _('Text'),
        }

    @cached_property
    def changes(self) -> dict[str, Any]:
        changes = super().changes
        # NOTE: The proposed text is stored as a plain string in the ticket,
        #       it would be escaped when set on the topic. Since it has been
        #       submitted through a public form, we sanitize it again.
        if isinstance(changes.get('text'), str):
            changes = {**changes, 'text': sanitize_html(changes['text'])}
        return changes

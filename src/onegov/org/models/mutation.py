from functools import cached_property
from onegov.agency.models.mutation import Mutation
from onegov.org.i18n import _
from onegov.page import PageCollection


from typing import TYPE_CHECKING
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

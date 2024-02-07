from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.gazette.observer import observes
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Sequence
    from onegov.gazette.models.notice import GazetteNotice
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import relationship


class Category(AdjacencyList, ContentMixin, TimestampMixin):

    """ Defines a category for official notices.

    Although the categories are defined as an adjacency list, we currently
    use it only as a simple alphabetically ordered key-value list (name-title).

    """

    __tablename__ = 'gazette_categories'

    #: True, if this category is still in use.
    active: 'Column[bool | None]' = Column(Boolean, nullable=True)

    if TYPE_CHECKING:
        # we need to override these attributes to get the correct base class
        parent: relationship['Category | None']
        children: relationship[Sequence['Category']]
        @property
        def root(self) -> 'Category': ...
        @property
        def ancestors(self) -> Iterator['Category']: ...

    def notices(self) -> 'Query[GazetteNotice]':
        """ Returns a query to get all notices related to this category. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._categories.has_key(self.name)  # type:ignore
        )

        return notices

    @property
    def in_use(self) -> bool:
        """ True, if the category is used by any notice. """

        if self.notices().first():
            return True

        return False

    @observes('title')
    def title_observer(self, title: str) -> None:
        """ Changes the category title of the notices when updating the title
        of the category.

        """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = self.notices()
        notices = notices.filter(
            or_(
                GazetteNotice.category.is_(None),
                GazetteNotice.category != title
            )
        )
        for notice in notices:
            notice.category = title

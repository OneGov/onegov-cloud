from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class Category(AdjacencyList, TimestampMixin):

    """ Defines a category for official notices.

    Although the categories are defined as an adjacency list, we currently
    use it only as a simple alphabetically ordered key-value list (name-title).

    """

    __tablename__ = 'gazette_categories'

    #: True, if this category is still in use.
    active = Column(Boolean, nullable=True)

    def in_use(self, session):
        """ True, if the category is used by any notice. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        query = session.query(GazetteNotice._categories)
        query = query.filter(
            GazetteNotice._categories.has_key(self.name)  # noqa
        )
        if query.first():
            return True

        return False

    @observes('title')
    def title_observer(self, title):
        """ Changes the category title of the notices when updating the title
        of the category.

        """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        query = object_session(self).query(GazetteNotice)
        query = query.filter(
            GazetteNotice._categories.has_key(self.name),  # noqa
            or_(
                GazetteNotice.category.is_(None),
                GazetteNotice.category != title
            )
        )
        for notice in query:
            notice.category = title

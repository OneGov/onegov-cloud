from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class Category(AdjacencyList, ContentMixin, TimestampMixin):

    """ Defines a category for official notices.

    Although the categories are defined as an adjacency list, we currently
    use it only as a simple alphabetically ordered key-value list (name-title).

    """

    __tablename__ = 'gazette_categories'

    #: True, if this category is still in use.
    active = Column(Boolean, nullable=True)

    def notices(self):
        """ Returns a query to get all notices related to this category. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._categories.has_key(self.name)  # noqa
        )

        return notices

    @property
    def in_use(self):
        """ True, if the category is used by any notice. """

        if self.notices().first():
            return True

        return False

    @observes('title')
    def title_observer(self, title):
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

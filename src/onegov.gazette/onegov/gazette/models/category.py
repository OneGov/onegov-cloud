from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class Category(AdjacencyList, ContentMixin, TimestampMixin):

    """ Defines a category for official notices.

    The name is used as key, the title as value.

    """

    __tablename__ = 'gazette_categories'

    #: True, if this category is still in use.
    active = Column(Boolean, nullable=True)

    #: The external category (the publisher's category)
    external = meta_property('external')

    @property
    def in_use(self):
        """ True, if the category is used by any notice. """
        from onegov.gazette.models.notice import GazetteNotice

        session = object_session(self)
        assert session

        for notice in session.query(GazetteNotice):
            if self.name == notice.category_id:
                return True

        return False

    @observes('title')
    def title_observer(self, title):
        from onegov.gazette.models.notice import GazetteNotice

        session = object_session(self)
        assert session

        for notice in session.query(GazetteNotice):
            if self.name == notice.category_id:
                if title != notice.category:
                    notice.category = title

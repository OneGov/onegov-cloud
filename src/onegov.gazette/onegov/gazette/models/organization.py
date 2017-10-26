from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class Organization(AdjacencyList, TimestampMixin):

    """ Defines an organization for official notices.

    Although the categories are defined as a flexible adjacency list, we
    currently use it only as a two-stage adjacency list key-value list
    (name-title).

    """

    __tablename__ = 'gazette_organizations'

    #: True, if this organization is still in use.
    active = Column(Boolean, nullable=True)

    def in_use(self, session):
        """ True, if the organization is used by any notice or has any child
        organizations.

        """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        if self.children:
            return True

        query = session.query(GazetteNotice._organizations)
        query = query.filter(
            GazetteNotice._organizations.has_key(self.name)  # noqa
        )
        if query.first():
            return True

        return False

    @observes('title')
    def title_observer(self, title):
        from onegov.gazette.models.notice import GazetteNotice  # circular

        query = object_session(self).query(GazetteNotice)
        query = query.filter(
            GazetteNotice._organizations.has_key(self.name),  # noqa
            or_(
                GazetteNotice.organization.is_(None),
                GazetteNotice.organization != title
            )
        )
        for notice in query:
            notice.organization = title

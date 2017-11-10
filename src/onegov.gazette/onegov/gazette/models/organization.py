from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import MoveDirection
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy_utils import observes
from sqlalchemy.orm import object_session


class Organization(AdjacencyList, ContentMixin, TimestampMixin):

    """ Defines an organization for official notices.

    Although the categories are defined as a flexible adjacency list, we
    currently use it only as a two-stage adjacency list key-value list
    (name-title).

    """

    __tablename__ = 'gazette_organizations'

    #: True, if this organization is still in use.
    active = Column(Boolean, nullable=True)

    external_name = meta_property('external_name')

    def notices(self):
        """ Returns a query to get all notices related to this category. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._organizations.has_key(self.name)  # noqa
        )

        return notices

    @property
    def in_use(self):
        """ True, if the organization is used by any notice. """

        if self.notices().first():
            return True

        return False

    @observes('title')
    def title_observer(self, title):
        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = self.notices()
        notices = notices.filter(
            or_(
                GazetteNotice.organization.is_(None),
                GazetteNotice.organization != title
            )
        )
        for notice in notices:
            notice.organization = title


class OrganizationMove(object):
    """ Represents a single move of an adjacency list item. """

    def __init__(self, session, subject_id, target_id, direction):
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    @classmethod
    def for_url_template(cls):
        return cls(
            session=None,
            subject_id='{subject_id}',
            target_id='{target_id}',
            direction='{direction}'
        )

    def execute(self):
        from onegov.gazette.collections import OrganizationCollection

        organizations = OrganizationCollection(self.session)
        subject = organizations.by_id(self.subject_id)
        target = organizations.by_id(self.target_id)
        if subject and target and subject != target:
            if subject.parent_id == target.parent_id:
                OrganizationCollection(self.session).move(
                    subject=subject,
                    target=target,
                    direction=getattr(MoveDirection, self.direction)
                )

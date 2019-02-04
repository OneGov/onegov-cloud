from onegov.core.crypto import random_token
from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.utils import normalize_for_url
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.file.utils import content_type_from_fileobj
from onegov.file.utils import extension_for_content_type
from onegov.people.models.membership import AgencyMembership
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text


class AgencyOrganigram(File):
    __mapper_args__ = {'polymorphic_identity': 'agency_organigram'}


class Agency(AdjacencyList, ContentMixin, TimestampMixin, ORMSearchable):
    """ An agency (organization) containing people through memberships. """

    __tablename__ = 'agencies'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': None,
    }

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
        'description': {'type': 'localized'},
        'portrait': {'type': 'localized_html'},
    }

    #: a short description of the agency
    description = Column(Text, nullable=True)

    #: describes the agency
    portrait = Column(Text, nullable=True)

    #: a reference to the organization chart
    organigram = associated(AgencyOrganigram, 'organigram', 'one-to-one')

    @property
    def organigram_file(self):
        """ Returns the file-like content of the organigram. """

        if self.organigram:
            return self.organigram.reference.file

    @organigram_file.setter
    def organigram_file(self, value):
        """ Sets the organigram, expects a file-like value. """

        filename = 'organigram-{}.{}'.format(
            normalize_for_url(self.title),
            extension_for_content_type(content_type_from_fileobj(value))
        )
        if self.organigram:
            self.organigram.reference = as_fileintent(value, filename)
            self.organigram.name = filename
        else:
            organigram = AgencyOrganigram(id=random_token())
            organigram.reference = as_fileintent(value, filename)
            organigram.name = filename
            self.organigram = organigram

    def add_person(self, person_id, title, **kwargs):
        """ Appends a person to the agency with the given title. """

        order = kwargs.pop('order', 2 ** 16)

        self.memberships.append(
            AgencyMembership(
                person_id=person_id,
                title=title,
                order=order,
                **kwargs
            )
        )

        for order, membership in enumerate(self.memberships):
            membership.order = order

    def sort_children(self, sortkey=None):
        """ Sorts the suborganizations.

        Sorts by the agency title by default.
        """

        def default_sortkey(agency):
            return normalize_for_url(agency.title)

        sortkey = sortkey or default_sortkey
        children = sorted(self.children, key=sortkey)
        for order, child in enumerate(children):
            child.order = order

    def sort_relationships(self, sortkey=None):
        """ Sorts the relationships.

        Sorts by last name, first name.by default.
        """

        def default_sortkey(membership):
            return normalize_for_url(membership.person.title)

        sortkey = sortkey or default_sortkey
        memberships = sorted(self.memberships.all(), key=sortkey)
        for order, membership in enumerate(memberships):
            membership.order = order

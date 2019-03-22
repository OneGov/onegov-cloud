from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4
from vobject import vCard
from vobject.vcard import Address
from vobject.vcard import Name


class Person(Base, ContentMixin, TimestampMixin, ORMSearchable):
    """ A person. """

    __tablename__ = 'people'

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
        'function': {'type': 'localized'},
        'email': {'type': 'text'},
    }

    @property
    def es_suggestion(self):
        return (self.title, f"{self.first_name} {self.last_name}")

    @property
    def title(self):
        """ Returns the Estern-ordered name. """

        return self.last_name + " " + self.first_name

    @property
    def spoken_title(self):
        """ Returns the Western-ordered name. Includes the academic title if
        available.

        """
        parts = []
        if self.academic_title:
            parts.append(self.academic_title)
        parts.append(self.first_name)
        parts.append(self.last_name)

        return " ".join(parts)

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the salutation used for the person
    salutation = Column(Text, nullable=True)

    #: the academic title of the person
    academic_title = Column(Text, nullable=True)

    #: the first name of the person
    first_name = Column(Text, nullable=False)

    #: the last name of the person
    last_name = Column(Text, nullable=False)

    #: when the person was born
    born = Column(Text, nullable=True)

    #: the professsion of the person
    profession = Column(Text, nullable=True)

    #: the function of the person
    function = Column(Text, nullable=True)

    #: the political party the person belongs to
    political_party = Column(Text, nullable=True)

    #: the parliamentary group the person belongs to
    parliamentary_group = Column(Text, nullable=True)

    #: an URL leading to a picture of the person
    picture_url = Column(Text, nullable=True)

    #: the email of the person
    email = Column(Text, nullable=True)

    #: the phone number of the person
    phone = Column(Text, nullable=True)

    #: the direct phone number of the person
    phone_direct = Column(Text, nullable=True)

    #: the website related to the person
    website = Column(Text, nullable=True)

    #: the address of the person
    address = Column(Text, nullable=True)

    #: some remarks about the person
    notes = Column(Text, nullable=True)

    def vcard(self, exclude=None):
        """ Returns the person as vCard (3.0).

        Allows to specify the included attributes, provides a reasonable
        default if none are specified. Always includes the first and last
        name.

        """
        exclude = exclude or ['notes']
        result = vCard()

        prefix = ""
        if 'academic_title' not in exclude and self.academic_title:
            prefix = self.academic_title

        # mandatory fields
        line = result.add('n')
        line.value = Name(
            prefix=prefix,
            given=self.first_name,
            family=self.last_name,
        )
        line.charset_param = 'utf-8'

        line = result.add('fn')
        line.value = " ".join((
            prefix, self.first_name, self.last_name
        )).strip()
        line.charset_param = 'utf-8'

        # optional fields
        if 'function' not in exclude and self.function:
            line = result.add('title')
            line.value = self.function
            line.charset_param = 'utf-8'

        if 'picture_url' not in exclude and self.picture_url:
            line = result.add('photo')
            line.value = self.picture_url

        if 'email' not in exclude and self.email:
            line = result.add('email')
            line.value = self.email

        if 'phone' not in exclude and self.phone:
            line = result.add('tel')
            line.value = self.phone

        if 'phone_direct' not in exclude and self.phone_direct:
            line = result.add('tel')
            line.value = self.phone_direct

        if 'website' not in exclude and self.website:
            line = result.add('url')
            line.value = self.website

        if 'address' not in exclude and self.address:
            line = result.add('adr')
            line.value = Address(street=self.address)
            line.charset_param = 'utf-8'

        if 'notes' not in exclude and self.notes:
            line = result.add('note')
            line.value = self.notes
            line.charset_param = 'utf-8'

        memberships = [
            ', '.join((m.agency.title, m.title)) for m in self.memberships
        ]
        if memberships:
            line = result.add('org')
            line.value = memberships
            line.charset_param = 'utf-8'

        return result.serialize()

    @property
    def memberships_by_agency(self):
        """ Returns the memberships sorted alphabetically by the agency. """

        def sortkey(membership):
            return membership.agency.title

        return sorted(self.memberships, key=sortkey)

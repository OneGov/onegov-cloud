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
        result.add('n').value = Name(
            prefix=prefix,
            given=self.first_name,
            family=self.last_name,
        )
        result.add('fn').value = " ".join((
            prefix, self.first_name, self.last_name
        )).strip()

        # optional fields
        if 'function' not in exclude and self.function:
            result.add('title').value = self.function
        if 'picture_url' not in exclude and self.picture_url:
            result.add('photo').value = self.picture_url
        if 'email' not in exclude and self.email:
            result.add('email').value = self.email
        if 'phone' not in exclude and self.phone:
            result.add('tel').value = self.phone
        if 'phone_direct' not in exclude and self.phone_direct:
            result.add('tel').value = self.phone_direct
        if 'website' not in exclude and self.website:
            result.add('url').value = self.website
        if 'address' not in exclude and self.address:
            result.add('adr').value = Address(street=self.address)
        if 'notes' not in exclude and self.notes:
            result.add('note').value = self.notes

        for membership in self.memberships:
            result.add('org').value = [
                membership.agency.title,
                membership.title
            ]

        return result.serialize()

    @property
    def memberships_by_agency(self):
        """ Returns the memberships sorted alphabetically by the agency. """

        def sortkey(membership):
            return membership.agency.title

        return sorted(self.memberships, key=sortkey)

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4


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
    def title(self):
        """ Returns the Estern-ordered name. """

        return self.last_name + " " + self.first_name

    @property
    def spoken_title(self):
        """ Returns the Western-ordered name. Includes the salutation if
        available.

        """

        if self.salutation:
            parts = self.salutation, self.first_name, self.last_name
        else:
            parts = self.first_name, self.last_name

        return " ".join(parts)

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the salutation used for the person
    salutation = Column(Text, nullable=True)

    #: the first name of the person
    first_name = Column(Text, nullable=False)

    #: the last name of the person
    last_name = Column(Text, nullable=False)

    #: the function of the person
    function = Column(Text, nullable=True)

    #: an URL leading to a picture of the person
    picture_url = Column(Text, nullable=True)

    #: the email of the person
    email = Column(Text, nullable=True)

    #: the phone number of the person
    phone = Column(Text, nullable=True)

    #: the website related to the person
    website = Column(Text, nullable=True)

    #: the address of the person
    address = Column(Text, nullable=True)

    #: some remarks about the person
    notes = Column(Text, nullable=True)

from onegov.core.orm import Base
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Text
from uuid import uuid4
# from sqlalchemy.orm import relationship


class Chat(Base, UTCPublicationMixin):
    """ A chat. """

    __tablename__ = 'chats'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
    }

    @property
    def es_suggestion(self):
        return (self.title, f"{self.first_name} {self.last_name}")

<<<<<<< Updated upstream
    @property
    def title(self):
        """ Returns the Estern-ordered name. """

        return "chat"  # TODO: Das ergendwie no apasse

=======
>>>>>>> Stashed changes
    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the specific items linked with this invoice
    # messages: 'relationship[list[Message]]' = relationship(
    #     Message, backref='message')

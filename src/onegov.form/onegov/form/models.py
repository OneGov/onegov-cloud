from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.form.parser import parse_form
from sqlalchemy import Boolean, Column, ForeignKeyConstraint, Integer, Text
from sqlalchemy.orm import deferred, relationship


class FormDefinition(Base, TimestampMixin):
    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    #: the name of the form, generated form the title if not provided
    name = Column(Text, nullable=False, primary_key=True)

    #: the revision of the form, basically a hash of the definition
    revision = Column(Text, nullable=False, primary_key=True)

    #: true if the form is a builtin form
    is_builtin = Column(Boolean, nullable=False)

    #: true if the form is available to the public
    is_available = Column(Boolean, nullable=False)

    #: metadata associated with the form, only for storing small amounts
    meta = Column(JSON, nullable=False, default=dict)

    #: content associated with the form, for storing things like long texts
    content = deferred(Column(JSON, nullable=False, default=dict))

    #: the form as parsable string
    definition = Column(Text, nullable=False)

    #: link between forms and submissions
    submissions = relationship('FormSubmission', backref='form')

    @property
    def form_class(self):
        """ Parses the form definition and returns a form class. """

        return parse_form(self.definition)


class FormSubmission(Base, TimestampMixin):
    """ Defines a submitted form in the database. """

    __tablename__ = 'submissions'

    #: internal id of the form submission
    id = Column(Integer, primary_key=True)

    #: name of the form this submission belongs to
    name = Column(Text, nullable=False)

    #: the revision of the form this submission belongs to
    revision = Column(Text, nullable=False)

    #: the submission data
    data = Column(JSON, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['name', 'revision'],
            [FormDefinition.name, FormDefinition.revision]
        ),
    )

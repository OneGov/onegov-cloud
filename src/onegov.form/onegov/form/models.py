from hashlib import md5
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.form.errors import UnableToComplete
from onegov.form.parser import parse_form
from sqlalchemy import Column, Enum, ForeignKey, Text
from sqlalchemy.orm import (
    deferred,
    relationship,
)
from sqlalchemy_utils import observes
from uuid import uuid4


def hash_definition(definition):
    return md5(definition.encode('utf-8')).hexdigest()


class FormDefinition(Base, TimestampMixin):
    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    #: the name of the form (key, part of the url)
    name = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title = Column(Text, nullable=False)

    #: metadata associated with the form, for storing small amounts of data
    meta = Column(JSON, nullable=False, default=dict)

    #: content associated with the form, for storing things like long texts
    content = deferred(Column(JSON, nullable=False, default=dict))

    #: the form as parsable string
    definition = Column(Text, nullable=False)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum = Column(Text, nullable=False)

    #: the type of the form, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    #: link between forms and submissions
    submissions = relationship('FormSubmission', backref='form')

    __mapper_args__ = {
        "polymorphic_on": 'type'
    }

    @property
    def form_class(self):
        """ Parses the form definition and returns a form class. """

        return parse_form(self.definition)

    @observes('definition')
    def definition_observer(self, definition):
        self.checksum = hash_definition(definition)


class FormSubmission(Base, TimestampMixin):
    """ Defines a submitted form in the database. """

    __tablename__ = 'submissions'

    #: id of the form submission
    id = Column(UUID, primary_key=True, default=uuid4)

    #: name of the form this submission belongs to
    name = Column(Text, ForeignKey(FormDefinition.name), nullable=False)

    #: the source code of the form at the moment of submission. This is stored
    #: alongside the submission as the original form may change later. We
    #: want to keep the old form around just in case.
    definition = Column(Text, nullable=False)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum = Column(Text, nullable=False)

    #: the submission data
    data = Column(JSON, nullable=False)

    #: the state of the submission
    state = Column(
        Enum('pending', 'complete', name='submission_state'),
        nullable=False
    )

    #: the files belonging to this submission
    files = relationship(
        "FormSubmissionFile",
        backref='submission',
        cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_on": 'state'
    }

    @property
    def form_class(self):
        """ Parses the form definition and returns a form class. """

        return parse_form(self.definition)

    @observes('definition')
    def definition_observer(self, definition):
        self.checksum = hash_definition(definition)

    def complete(self):
        """ Changes the state to 'complete', if the data is valid. """

        if not self.form_class(data=self.data).validate():
            raise UnableToComplete()

        self.state = 'complete'

    def prune(self, form=None):
        """ Pending submissions are not necessarily valid. This function
        removes the invalid bits from the data if called.

        On 'completed' submissions it has no effect.

        """
        if self.state == 'pending':

            if not form:
                form = self.form_class(data=self.data)
                form.validate()

            for field_id in form.errors:
                if field_id in self.data:
                    del self.data[field_id]
                    form._fields[field_id].data = ''


class PendingFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'pending'}


class CompleteFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'complete'}


class FormSubmissionFile(Base, TimestampMixin):
    """ Holds files uploaded in form submissions.

    This ensures that forms can be loaded without having to load the files
    into memory. But it's still not super efficient. The thinking is that
    most forms won't have file uploads and if they do it won't be large.

    Don't store big files here, or files which need to be served often.
    For that you *have* to use some kind of filesystem storage.

    The basic use case for this table is the odd table which contains some
    kind of file which is then viewed by backend personell only.

    In this case there won't many file downloads and it's important
    that the file stays with the form and is not accidentally lost.

    So it fits for that case.
    """

    __tablename__ = 'submission_files'

    #: id of the file
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the id of the submission
    submission_id = Column(UUID, ForeignKey(FormSubmission.id), nullable=False)

    #: the id of the field in the submission
    field_id = Column(Text, nullable=False)

    #: the actual file data
    filedata = deferred(Column(Text, nullable=False))

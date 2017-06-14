import html

from hashlib import md5
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm.types import UTCDateTime
from onegov.form.display import render_field
from onegov.form.parser import parse_form
from onegov.pay import Payable
from onegov.pay import process_payment
from onegov.search import ORMSearchable
from sedate import utcnow
from sqlalchemy import Column, Enum, ForeignKey, Text
from sqlalchemy.orm import (
    deferred,
    object_session,
    relationship,
)
from sqlalchemy_utils import observes
from uuid import uuid4
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import EmailField


def hash_definition(definition):
    return md5(definition.encode('utf-8')).hexdigest()


class SearchableDefinition(ORMSearchable):
    """ Defines how the definitions are searchable. For now, submissions are
    not searched as they are usually accessed through the ticket, at least in
    onegov.town. If other modules need this, it can be added here and
    onegov.town can decied not to search for submissions.

    """
    es_id = 'name'
    es_public = True

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'}
    }

    @property
    def es_language(self):
        return 'de'  # XXX add to database in the future


class FormDefinition(Base, ContentMixin, TimestampMixin, SearchableDefinition):
    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    #: the name of the form (key, part of the url)
    name = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title = Column(Text, nullable=False)

    #: the form as parsable string
    definition = Column(Text, nullable=False)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum = Column(Text, nullable=False)

    #: the type of the form, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    #: link between forms and submissions
    submissions = relationship('FormSubmission', backref='form')

    #: lead text describing the form
    lead = meta_property('lead')

    #: content associated with the form
    text = content_property('text')

    #: payment options ('manual' for out of band payments without cc, 'free'
    #: for both manual and cc payments, 'cc' for forced cc payments)
    payment_method = content_property('payment_method')

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

    def has_submissions(self, with_state=None):
        query = object_session(self).query(FormSubmission.id)
        query = query.filter(FormSubmission.name == self.name)

        if with_state is not None:
            query = query.filter(FormSubmission.state == with_state)

        return query.first() and True or False


class FormSubmission(Base, TimestampMixin, Payable):
    """ Defines a submitted form in the database. """

    __tablename__ = 'submissions'

    #: id of the form submission
    id = Column(UUID, primary_key=True, default=uuid4)

    #: name of the form this submission belongs to
    name = Column(Text, ForeignKey(FormDefinition.name), nullable=True)

    #: the title of the submission, generated from the submitted fields
    #: NULL for submissions which are not complete
    title = Column(Text, nullable=True)

    #: the e-mail address associated with the submitee, generated from the
    # submitted fields (may be NULL, even for complete submissions)
    email = Column(Text, nullable=True)

    #: the source code of the form at the moment of submission. This is stored
    #: alongside the submission as the original form may change later. We
    #: want to keep the old form around just in case.
    definition = Column(Text, nullable=False)

    #: the exact time this submissions was changed from 'pending' to 'complete'
    received = Column(UTCDateTime, nullable=True)

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

    @property
    def form_obj(self):
        """ Returns a form instance containing the submission data. """

        return self.form_class(data=self.data)

    def get_email_field_data(self, form=None):
        form = form or self.form_obj

        email_fields = form.match_fields(
            include_classes=(EmailField, ),
            required=True,
            limit=1
        )
        email_fields += form.match_fields(
            include_classes=(EmailField, ),
            required=False,
            limit=1
        )

        if email_fields:
            return form._fields[email_fields[0]].data

    @observes('definition')
    def definition_observer(self, definition):
        self.checksum = hash_definition(definition)

    @observes('state')
    def state_observer(self, state):
        if self.state == 'complete':
            form = self.form_class(data=self.data)

            title_fields = form.match_fields(
                include_classes=(StringField, ),
                exclude_classes=(TextAreaField, ),
                required=True,
                limit=3
            )

            if title_fields:
                self.title = ', '.join(
                    html.unescape(render_field(form._fields[id]))
                    for id in title_fields
                )

            self.email = self.get_email_field_data(form=form)

            # only set the date the first time around
            if not self.received:
                self.received = utcnow()

    def process_payment(self, price, provider=None, token=None):
        """ Takes a request, optionally with the provider and the token
        by the provider that can be used to charge the credit card and creates
        a payment record if necessary.

        Returns True or a payment object if the payment was processed
        successfully. That is, if there is a payment or if there is no payment
        required the method returns truthy.

        """

        if price and price.amount > 0:
            return process_payment(
                self.form.payment_method, price, provider, token)

        return True


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

    @property
    def submission_data(self):
        """ Returns the data stored on the submission, associated with this
        submisison file.

        """
        return self.submission.data.get(self.field_id)

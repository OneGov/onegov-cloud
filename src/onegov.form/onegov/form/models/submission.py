import html

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm.types import UTCDateTime
from onegov.file import AssociatedFiles, File
from onegov.form.display import render_field
from onegov.form.parser import parse_form
from onegov.form.utils import extract_text_from_html, hash_definition
from onegov.form.extensions import Extendable
from onegov.pay import Payable
from onegov.pay import process_payment
from sedate import utcnow
from sqlalchemy import Column, Enum, ForeignKey, Text
from sqlalchemy_utils import observes
from uuid import uuid4
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import EmailField


class FormSubmission(Base, TimestampMixin, Payable, AssociatedFiles,
                     Extendable):
    """ Defines a submitted form in the database. """

    __tablename__ = 'submissions'

    #: id of the form submission
    id = Column(UUID, primary_key=True, default=uuid4)

    #: name of the form this submission belongs to
    name = Column(Text, ForeignKey("forms.name"), nullable=True)

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

    #: metadata about this submission
    meta = Column(JSON, nullable=False)

    #: the submission data
    data = Column(JSON, nullable=False)

    #: the state of the submission
    state = Column(
        Enum('pending', 'complete', name='submission_state'),
        nullable=False
    )

    #: payment options -> copied from the dfinition at the moment of
    #: submission. This is stored alongside the submission as the original
    #: form setting may change later.
    payment_method = Column(Text, nullable=False, default='manual')

    __mapper_args__ = {
        "polymorphic_on": 'state'
    }

    @property
    def form_class(self):
        """ Parses the form definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition), self.meta.get('extensions'))

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
                self.title = extract_text_from_html(', '.join(
                    html.unescape(render_field(form._fields[id]))
                    for id in title_fields
                ))

            if not self.email:
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
            return process_payment(self.payment_method, price, provider, token)

        return True


class PendingFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'pending'}


class CompleteFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'complete'}


class FormFile(File):
    __mapper_args__ = {'polymorphic_identity': 'formfile'}

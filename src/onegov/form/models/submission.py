from __future__ import annotations

import html

from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import TimestampMixin, dict_property, meta_property
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm.types import UTCDateTime
from onegov.file import AssociatedFiles, File
from onegov.form.display import render_field
from onegov.form.extensions import Extendable
from onegov.form.parser import parse_form
from onegov.form.utils import extract_text_from_html
from onegov.form.utils import hash_definition
from onegov.pay import Payable
from onegov.pay import process_payment
from sedate import utcnow
from sqlalchemy import case
from sqlalchemy import CheckConstraint
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4
from wtforms.fields import EmailField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from onegov.form import Form
    from onegov.form.models import FormDefinition, FormRegistrationWindow
    from onegov.form.models import SurveyDefinition, SurveySubmissionWindow
    from onegov.form.types import RegistrationState, SubmissionState
    from onegov.pay import Payment, PaymentError, PaymentProvider, Price
    from onegov.pay.types import PaymentMethod


class FormSubmission(Base, TimestampMixin, Payable, AssociatedFiles,
                     Extendable):

    """ Defines a submitted form of any kind in the database. """

    __tablename__ = 'submissions'

    #: id of the form submission
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: name of the form this submission belongs to
    name: Column[str | None] = Column(
        Text,
        ForeignKey('forms.name'),
        nullable=True
    )

    #: the form this submission belongs to
    form: relationship[FormDefinition | None] = relationship(
        'FormDefinition',
        back_populates='submissions'
    )

    #: the title of the submission, generated from the submitted fields
    #: NULL for submissions which are not complete
    title: Column[str | None] = Column(Text, nullable=True)

    #: the e-mail address associated with the submitee, generated from the
    # submitted fields (may be NULL, even for complete submissions)
    email: Column[str | None] = Column(Text, nullable=True)

    #: the source code of the form at the moment of submission. This is stored
    #: alongside the submission as the original form may change later. We
    #: want to keep the old form around just in case.
    definition: Column[str] = Column(Text, nullable=False)

    #: the exact time this submissions was changed from 'pending' to 'complete'
    received: Column[datetime | None] = Column(UTCDateTime, nullable=True)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum: Column[str] = Column(Text, nullable=False)

    #: metadata about this submission
    meta: Column[dict[str, Any]] = Column(JSON, nullable=False)

    #: the submission data
    data: Column[dict[str, Any]] = Column(JSON, nullable=False)

    #: the state of the submission
    state: Column[SubmissionState] = Column(
        Enum('pending', 'complete', name='submission_state'),  # type:ignore
        nullable=False
    )

    #: the number of spots this submission wants to claim
    #: (only relevant if there's a registration window)
    spots: Column[int] = Column(Integer, nullable=False, default=0)

    #: the number of spots this submission has actually received
    #: None => the decision if spots should be given is still open
    #: 0 => the decision was negative, no spots were given
    #: 1-x => the decision was positive, at least some spots were given
    claimed: Column[int | None] = Column(
        Integer,
        nullable=True,
        default=None
    )

    #: the id of the registration window linked with this submission
    registration_window_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('registration_windows.id'),
        nullable=True
    )

    #: the registration window linked with this submission
    registration_window: relationship[FormRegistrationWindow | None]
    registration_window = relationship(
        'FormRegistrationWindow',
        back_populates='submissions'
    )

    #: payment options -> copied from the definition at the moment of
    #: submission. This is stored alongside the submission as the original
    #: form setting may change later.
    payment_method: Column[PaymentMethod] = Column(
        Text,  # type:ignore[arg-type]
        nullable=False,
        default='manual'
    )
    minimum_price_total: dict_property[float | None] = meta_property()

    #: extensions
    extensions: dict_property[list[str]] = meta_property(default=list)

    __table_args__ = (
        CheckConstraint(
            'COALESCE(claimed, 0) <= spots',
            name='claimed_no_more_than_requested'
        ),
    )

    @property
    def form_class(self) -> type[Form]:
        """ Parses the form definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition),
            self.extensions or []
        )

    @property
    def form_obj(self) -> Form:
        """ Returns a form instance containing the submission data. """
        return self.form_class(data=self.data)

    def get_email_field_data(self, form: Form | None = None) -> str | None:
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
        return None

    @observes('definition')
    def definition_observer(self, definition: str) -> None:
        self.checksum = hash_definition(definition)

    @observes('state')
    def state_observer(self, state: SubmissionState) -> None:
        if self.state == 'complete':
            form = self.form_class(data=self.data)

            self.update_title(form)

            if not self.email:
                self.email = self.get_email_field_data(form=form)

            # only set the date the first time around
            if not self.received:
                self.received = utcnow()

    def update_title(self, form: Form) -> None:
        title_fields = form.title_fields
        if title_fields:
            # NOTE: Since the title won't be rendered as Markup, it is
            #       safe to unescape before extracting text, this will
            #       avoid escaped html entities in the title
            self.title = extract_text_from_html(', '.join(
                html.unescape(render_field(form._fields[id]))
                for id in title_fields
            ))

    #: Additional information about the submitee
    submitter_name: dict_property[str | None] = meta_property()
    submitter_address: dict_property[str | None] = meta_property()
    submitter_phone: dict_property[str | None] = meta_property()
    __mapper_args__ = {
        'polymorphic_on': 'state'
    }

    if TYPE_CHECKING:
        # HACK: hybrid_property won't work otherwise until 2.0
        registration_state: Column[RegistrationState | None]
    else:
        @hybrid_property
        def registration_state(self) -> RegistrationState | None:
            if not self.spots:
                return None
            if self.claimed is None:
                return 'open'
            if self.claimed == 0:
                return 'cancelled'
            if self.claimed == self.spots:
                return 'confirmed'
            if self.claimed < self.spots:
                return 'partial'
            return None

        @registration_state.expression  # type:ignore[no-redef]
        def registration_state(cls):
            return case((
                (cls.spots == 0, None),
                (cls.claimed == None, 'open'),
                (cls.claimed == 0, 'cancelled'),
                (cls.claimed == cls.spots, 'confirmed'),
                (cls.claimed < cls.spots, 'partial')
            ), else_=None)

    @property
    def payable_reference(self) -> str:
        assert self.received is not None
        if self.name:
            return f'{self.name}/{self.title}@{self.received.isoformat()}'
        else:
            return f'{self.title}@{self.received.isoformat()}'

    def process_payment(
        self,
        price: Price | None,
        provider: PaymentProvider[Any] | None = None,
        token: str | None = None
    ) -> Payment | PaymentError | bool | None:
        """ Takes a request, optionally with the provider and the token
        by the provider that can be used to charge the credit card and creates
        a payment record if necessary.

        Returns True or a payment object if the payment was processed
        successfully. That is, if there is a payment or if there is no payment
        required the method returns truthy.

        """

        if price and price.amount > 0:
            payment_method: PaymentMethod
            if price.credit_card_payment is True:
                payment_method = 'cc'
            else:
                payment_method = self.payment_method
            return process_payment(payment_method, price, provider, token)

        return True

    def claim(self, spots: int | None = None) -> bool:
        """ Claimes the given number of spots (defaults to the requested
        number of spots).

        :return bool: Whether or not claiming spots is possible
        """
        spots = spots or self.spots

        assert self.registration_window

        if self.registration_window.limit:
            limit = self.registration_window.limit
            claimed = self.registration_window.claimed_spots

            # check if limit of participants is reached
            if spots > (limit - claimed):
                return False

            assert spots <= (limit - claimed)

        claimed_spots = (self.claimed or 0) + spots
        assert claimed_spots <= self.spots
        self.claimed = claimed_spots
        return True

    def disclaim(self, spots: int | None = None) -> None:
        """ Disclaims the given number of spots (defaults to all spots that
        were claimed so far).

        """
        spots = spots or self.spots

        assert self.registration_window

        if self.claimed is None:
            self.claimed = 0
        else:
            self.claimed = max(0, self.claimed - spots)


class SurveySubmission(Base, TimestampMixin, AssociatedFiles,
                       Extendable):
    """ Defines a submitted survey of any kind in the database. """

    __tablename__ = 'survey_submissions'

    #: id of the form submission
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: name of the survey this submission belongs to
    name: Column[str | None] = Column(
        Text,
        ForeignKey('surveys.name'),
        nullable=True
    )

    #: the survey this submission belongs to
    survey: relationship[SurveyDefinition | None] = relationship(
        'SurveyDefinition',
        back_populates='submissions'
    )

    #: the source code of the form at the moment of submission. This is stored
    #: alongside the submission as the original form may change later. We
    #: want to keep the old form around just in case.
    definition: Column[str] = Column(Text, nullable=False)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum: Column[str] = Column(Text, nullable=False)

    #: metadata about this submission
    meta: Column[dict[str, Any]] = Column(JSON, nullable=False)

    #: the submission data
    data: Column[dict[str, Any]] = Column(JSON, nullable=False)

    #: the id of the submission window linked with this submission
    submission_window_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('submission_windows.id'),
        nullable=True
    )

    #: the submission window linked with this submission
    submission_window: relationship[SurveySubmissionWindow | None]
    submission_window = relationship(
        'SurveySubmissionWindow',
        back_populates='submissions'
    )

    #: extensions
    extensions: dict_property[list[str]] = meta_property(default=list)

    @property
    def form_class(self) -> type[Form]:
        """ Parses the form definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition),
            self.extensions or []
        )

    @property
    def form_obj(self) -> Form:
        """ Returns a form instance containing the submission data. """
        return self.form_class(data=self.data)

    @observes('definition')
    def definition_observer(self, definition: str) -> None:
        self.checksum = hash_definition(definition)

    def update_title(self, survey: Form) -> None:
        title_fields = survey.title_fields
        if title_fields:
            # FIXME: Reconsider using unescape when consistently using Markup.
            self.title = extract_text_from_html(', '.join(
                html.unescape(render_field(survey._fields[id]))
                for id in title_fields
            ))


class PendingFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'pending'}


class CompleteFormSubmission(FormSubmission):
    __mapper_args__ = {'polymorphic_identity': 'complete'}


class FormFile(File):
    __mapper_args__ = {'polymorphic_identity': 'formfile'}

    @property
    def access(self) -> str:
        # we don't want these files to show up in search engines
        return 'secret' if self.published else 'private'

from __future__ import annotations

from wtforms import RadioField
from onegov.core.orm import Base, observes
from onegov.core.orm.mixins import (
    ContentMixin, TimestampMixin,
    content_property, dict_markup_property, dict_property, meta_property)
from onegov.core.utils import normalize_for_url
from onegov.file import MultiAssociatedFiles
from onegov.form.fields import MultiCheckboxField
from onegov.form.models.submission import FormSubmission, SurveySubmission
from onegov.form.models.registration_window import FormRegistrationWindow
from onegov.form.models.survey_window import SurveySubmissionWindow
from onegov.form.parser import parse_form
from onegov.form.utils import hash_definition
from onegov.form.extensions import Extendable
from sqlalchemy import Column, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relationship


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    # type gets shadowed in the model so we need an alias
    from builtins import type as type_t
    from uuid import UUID
    from datetime import date
    from onegov.form import Form
    from onegov.form.types import SubmissionState
    from onegov.pay.types import PaymentMethod
    from typing import Self
    from onegov.core.request import CoreRequest


class FormDefinition(Base, ContentMixin, TimestampMixin,
                     Extendable, MultiAssociatedFiles):

    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    # for better compatibility with generic code that expects an id
    # this is just an alias for `name`, which is our primary key
    @hybrid_property
    def id(self) -> str:
        return self.name

    #: the name of the form (key, part of the url)
    name: Column[str] = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title: Column[str] = Column(Text, nullable=False)

    #: the form as parsable string
    definition: Column[str] = Column(Text, nullable=False)

    #: hint on how to get to the resource
    pick_up: dict_property[str | None] = content_property()

    #: the group to which this resource belongs to (may be any kind of string)
    group: Column[str | None] = Column(Text, nullable=True)

    #: The normalized title for sorting
    order: Column[str] = Column(Text, nullable=False, index=True)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum: Column[str] = Column(Text, nullable=False)

    #: the type of the form, this can be used to create custom polymorphic
    #: subclasses. See `<https://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: link between forms and submissions
    submissions: relationship[list[FormSubmission]] = relationship(
        FormSubmission,
        back_populates='form'
    )

    #: link between forms and registration windows
    registration_windows: relationship[list[FormRegistrationWindow]] = (
        relationship(
            FormRegistrationWindow,
            back_populates='form',
            order_by='FormRegistrationWindow.start',
            cascade='all, delete-orphan'
        )
    )

    #: the currently active registration window
    #:
    #: this sorts the registration windows by the smaller k-nearest neighbour
    #: result of both start and end in relation to the current date
    #:
    #: the result is the *nearest* date range in relation to today:
    #:
    #: * during an active registration window, it's that active window
    #: * outside of active windows, it's last window half way until
    #:   the next window starts
    #:
    #: this could of course be done more conventionally, but this is cooler 😅
    #:
    current_registration_window: (
        relationship)[FormRegistrationWindow | None] = (
        relationship(
            'FormRegistrationWindow', viewonly=True, uselist=False,
            primaryjoin="""and_(
                FormRegistrationWindow.name == FormDefinition.name,
                FormRegistrationWindow.id == select((
                    FormRegistrationWindow.id,
                )).where(
                    FormRegistrationWindow.name == FormDefinition.name
                ).order_by(
                    func.least(
                        cast(
                            func.now().op('AT TIME ZONE')(
                                FormRegistrationWindow.timezone
                            ), Date
                        ).op('<->')(FormRegistrationWindow.start),
                        cast(
                            func.now().op('AT TIME ZONE')(
                                FormRegistrationWindow.timezone
                            ), Date
                        ).op('<->')(FormRegistrationWindow.end)
                    )
                ).limit(1).scalar_subquery()
            )"""
        )
    )

    #: lead text describing the form
    lead: dict_property[str | None] = meta_property()

    #: content associated with the form
    text = dict_markup_property('content')

    #: extensions
    extensions: dict_property[list[str]] = meta_property(default=list)

    #: payment options ('manual' for out of band payments without cc, 'free'
    #: for both manual and cc payments, 'cc' for forced cc payments)
    payment_method: Column[PaymentMethod] = Column(
        Text,  # type:ignore[arg-type]
        nullable=False,
        default='manual'
    )

    #: the minimum price total a form submission must exceed in order to
    #: be submitted
    minimum_price_total: dict_property[float | None] = meta_property()

    #: the reply_to address to supersede the global reply_to address for
    #: tickets created through this form
    reply_to: dict_property[str | None] = meta_property()

    custom_above_footer: dict_property[str | None] = meta_property()

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    @property
    def form_class(self) -> type_t[Form]:
        """ Parses the form definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition),
            self.extensions or [],
        )

    @observes('definition')
    def definition_observer(self, definition: str) -> None:
        self.checksum = hash_definition(definition)

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)

    def has_submissions(
        self,
        with_state: SubmissionState | None = None
    ) -> bool:

        session = object_session(self)
        query = session.query(FormSubmission.id)
        query = query.filter(FormSubmission.name == self.name)

        if with_state is not None:
            query = query.filter(FormSubmission.state == with_state)

        return session.query(query.exists()).scalar()

    def add_registration_window(
        self,
        start: date,
        end: date,
        *,
        enabled: bool = True,
        timezone: str = 'Europe/Zurich',
        limit: int | None = None,
        overflow: bool = True
    ) -> FormRegistrationWindow:

        window = FormRegistrationWindow(
            start=start,
            end=end,
            enabled=enabled,
            timezone=timezone,
            limit=limit,
            overflow=overflow
        )
        self.registration_windows.append(window)
        return window

    def for_new_name(self, name: str) -> Self:
        return self.__class__(
            name=name,
            title=self.title,
            definition=self.definition,
            group=self.group,
            order=self.order,
            checksum=self.checksum,
            type=self.type,
            meta=self.meta,
            content=self.content,
            payment_method=self.payment_method,
            created=self.created
        )


class SurveyDefinition(Base, ContentMixin, TimestampMixin,
                       Extendable):
    """ Defines a survey stored in the database. """

    __tablename__ = 'surveys'

    # # for better compatibility with generic code that expects an id
    # # this is just an alias for `name`, which is our primary key
    @hybrid_property
    def id(self) -> str:
        return self.name

    #: the name of the form (key, part of the url)
    name: Column[str] = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title: Column[str] = Column(Text, nullable=False)

    #: the form as parsable string
    definition: Column[str] = Column(Text, nullable=False)

    #: the group to which this resource belongs to (may be any kind of string)
    group: Column[str | None] = Column(Text, nullable=True)

    #: The normalized title for sorting
    order: Column[str] = Column(Text, nullable=False, index=True)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum: Column[str] = Column(Text, nullable=False)

    #: link between surveys and submissions
    submissions: relationship[list[SurveySubmission]] = relationship(
        SurveySubmission,
        back_populates='survey'
    )

    #: link between surveys and submission windows
    submission_windows: relationship[list[SurveySubmissionWindow]] = (
        relationship(
            SurveySubmissionWindow,
            back_populates='survey',
            order_by='SurveySubmissionWindow.start',
            cascade='all, delete-orphan'
        )
    )

    current_submission_window: relationship[SurveySubmissionWindow | None] = (
        relationship(
            'SurveySubmissionWindow',
            viewonly=True,
            uselist=False,
            primaryjoin="""and_(
                SurveySubmissionWindow.name == SurveyDefinition.name,
                SurveySubmissionWindow.id == select((
                    SurveySubmissionWindow.id,
                )).where(
                    SurveySubmissionWindow.name == SurveyDefinition.name
                ).order_by(
                    func.least(
                        cast(
                            func.now().op('AT TIME ZONE')(
                                SurveySubmissionWindow.timezone
                            ), Date
                        ).op('<->')(SurveySubmissionWindow.start),
                        cast(
                            func.now().op('AT TIME ZONE')(
                                SurveySubmissionWindow.timezone
                            ), Date
                        ).op('<->')(SurveySubmissionWindow.end)
                    )
                ).limit(1).scalar_subquery()
            )""",
        )
    )

    #: lead text describing the survey
    lead: dict_property[str | None] = meta_property()

    #: content associated with the Survey
    text = dict_markup_property('content')

    #: extensions
    extensions: dict_property[list[str]] = meta_property(default=list)

    @property
    def form_class(self) -> type[Form]:
        """ Parses the survey definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition),
            self.extensions or [],
        )

    @observes('definition')
    def definition_observer(self, definition: str) -> None:
        self.checksum = hash_definition(definition)

    @observes('title')
    def title_observer(self, title: str) -> None:
        self.order = normalize_for_url(title)

    def has_submissions(
        self,
    ) -> bool:

        session = object_session(self)
        query = session.query(SurveySubmission.id)
        query = query.filter(SurveySubmission.name == self.name)

        return session.query(query.exists()).scalar()

    def add_submission_window(
        self,
        start: date,
        end: date,
        *,
        enabled: bool = True,
        timezone: str = 'Europe/Zurich',
    ) -> SurveySubmissionWindow:

        window = SurveySubmissionWindow(
            start=start,
            end=end,
            enabled=enabled,
            timezone=timezone,
        )
        self.submission_windows.append(window)
        return window

    def get_results(self, request: CoreRequest, sw_id: (UUID | None) = None
                    ) -> dict[str, Any]:
        """ Returns the results of the survey. """

        form = request.get_form(self.form_class)

        all_fields = form._fields
        all_fields.pop('csrf_token', None)
        fields = all_fields.values()
        q = request.session.query(SurveySubmission).filter_by(name=self.name)
        if sw_id:
            submissions = q.filter_by(submission_window_id=sw_id).all()
        else:
            submissions = q.all()
        results: dict[str, Any] = {}

        aggregated = ['MultiCheckboxField', 'RadioField']

        for field in fields:
            if field.type not in aggregated:
                results[field.id] = []
            elif isinstance(field, (MultiCheckboxField, RadioField)):
                results[field.id] = {}
                for choice in field.choices:
                    results[field.id][choice[0]] = 0

        for submission in submissions:
            for field in fields:
                if submission.data.get(field.id):
                    if field.type not in aggregated:
                        results[field.id].append(
                            str(submission.data.get(field.id)))
                    else:
                        if isinstance(field, (RadioField)):
                            for choice in field.choices:
                                if choice[0] == submission.data.get(field.id,
                                                                    []):
                                    results[field.id][choice[0]] += 1
                        if isinstance(field, (MultiCheckboxField)):
                            for choice in field.choices:
                                if choice[0] in submission.data.get(field.id,
                                                                    []):
                                    results[field.id][choice[0]] += 1

        return results

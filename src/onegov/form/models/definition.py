from onegov.core.orm import Base
from onegov.core.orm.mixins import (
    ContentMixin, TimestampMixin,
    content_property, dict_property, meta_property)
from onegov.core.utils import normalize_for_url
from onegov.form.models.submission import FormSubmission
from onegov.form.models.registration_window import FormRegistrationWindow
from onegov.form.parser import parse_form
from onegov.form.utils import hash_definition
from onegov.form.extensions import Extendable
from sqlalchemy import Column, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session, relationship
from sqlalchemy_utils import observes


# type gets shadowed in the model so we need an alias
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.form import Form
    from onegov.form.types import SubmissionState
    from onegov.pay.types import PaymentMethod
    from typing_extensions import Self


class FormDefinition(Base, ContentMixin, TimestampMixin, Extendable):
    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    # for better compatibility with generic code that expects an id
    # this is just an alias for `name`, which is our primary key
    @hybrid_property
    def id(self) -> str:
        return self.name

    #: the name of the form (key, part of the url)
    name: 'Column[str]' = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title: 'Column[str]' = Column(Text, nullable=False)

    #: the form as parsable string
    definition: 'Column[str]' = Column(Text, nullable=False)

    #: hint on how to get to the resource
    pick_up: dict_property[str | None] = content_property()

    #: the group to which this resource belongs to (may be any kind of string)
    group: 'Column[str | None]' = Column(Text, nullable=True)

    #: The normalized title for sorting
    order: 'Column[str]' = Column(Text, nullable=False, index=True)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum: 'Column[str]' = Column(Text, nullable=False)

    #: the type of the form, this can be used to create custom polymorphic
    #: subclasses. See `<https://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type: 'Column[str]' = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    #: link between forms and submissions
    submissions: 'relationship[list[FormSubmission]]' = relationship(
        FormSubmission,
        backref='form'
    )

    #: link between forms and registration windows
    registration_windows: 'relationship[list[FormRegistrationWindow]]'
    registration_windows = relationship(
        FormRegistrationWindow,
        backref='form',
        order_by='FormRegistrationWindow.start',
        cascade='all, delete-orphan'
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
    current_registration_window: 'relationship[FormRegistrationWindow | None]'
    current_registration_window = relationship(
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
            ).limit(1)
        )"""
    )

    #: lead text describing the form
    lead: dict_property[str | None] = meta_property()

    #: content associated with the form
    text: dict_property[str | None] = content_property()

    #: extensions
    extensions: dict_property[list[str]] = meta_property(default=list)

    #: payment options ('manual' for out of band payments without cc, 'free'
    #: for both manual and cc payments, 'cc' for forced cc payments)
    payment_method: 'Column[PaymentMethod]' = Column(
        Text,  # type:ignore[arg-type]
        nullable=False,
        default='manual'
    )

    #: the minimum price total a form submission must exceed in order to
    #: be submitted
    minimum_price_total: dict_property[float | None] = meta_property()

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'generic'
    }

    @property
    def form_class(self) -> Type['Form']:
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
        with_state: 'SubmissionState | None' = None
    ) -> bool:

        session = object_session(self)
        query = session.query(FormSubmission.id)
        query = query.filter(FormSubmission.name == self.name)

        if with_state is not None:
            query = query.filter(FormSubmission.state == with_state)

        return session.query(query.exists()).scalar()

    def add_registration_window(
        self,
        start: 'date',
        end: 'date',
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

    def for_new_name(self, name: str) -> 'Self':
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

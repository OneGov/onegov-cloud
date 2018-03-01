from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import normalize_for_url
from onegov.form.models.submission import FormSubmission
from onegov.form.models.registration_window import FormRegistrationWindow
from onegov.form.parser import parse_form
from onegov.form.utils import hash_definition
from onegov.form.extensions import Extendable
from onegov.search import ORMSearchable
from sqlalchemy import Column, Text
from sqlalchemy.orm import object_session, relationship
from sqlalchemy_utils import observes


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


class FormDefinition(Base, ContentMixin, TimestampMixin, SearchableDefinition,
                     Extendable):
    """ Defines a form stored in the database. """

    __tablename__ = 'forms'

    #: the name of the form (key, part of the url)
    name = Column(Text, nullable=False, primary_key=True)

    #: the title of the form
    title = Column(Text, nullable=False)

    #: the form as parsable string
    definition = Column(Text, nullable=False)

    #: the group to which this resource belongs to (may be any kind of string)
    group = Column(Text, nullable=True)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    #: the checksum of the definition, forms and submissions with matching
    #: checksums are guaranteed to have the exact same definition
    checksum = Column(Text, nullable=False)

    #: the type of the form, this can be used to create custom polymorphic
    #: subclasses. See `<http://docs.sqlalchemy.org/en/improve_toc/
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    #: link between forms and submissions
    submissions = relationship('FormSubmission', backref='form')

    #: link between forms and registration windows
    registration_windows = relationship(
        'FormRegistrationWindow',
        backref='form',
        order_by='FormRegistrationWindow.start')

    #: the currently active registration window
    #:
    #: this sorts the registration windows by the smaller k-nearest neighbour
    #: result of both start and end in relation to the current date
    #:
    #: the result is the *nearest* date range in relation to today:
    #: * during an active registration window, it's that active window
    #: * outside of active windows, it's last window half way until
    #:   the next window starts
    #:
    #: this could of course be done more conventionally, but this is cooler 😅
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
    lead = meta_property()

    #: content associated with the form
    text = content_property()

    #: payment options ('manual' for out of band payments without cc, 'free'
    #: for both manual and cc payments, 'cc' for forced cc payments)
    payment_method = Column(Text, nullable=False, default='manual')

    __mapper_args__ = {
        "polymorphic_on": 'type'
    }

    @property
    def form_class(self):
        """ Parses the form definition and returns a form class. """

        return self.extend_form_class(
            parse_form(self.definition), self.meta.get('extensions'))

    @observes('definition')
    def definition_observer(self, definition):
        self.checksum = hash_definition(definition)

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)

    def has_submissions(self, with_state=None):
        query = object_session(self).query(FormSubmission.id)
        query = query.filter(FormSubmission.name == self.name)

        if with_state is not None:
            query = query.filter(FormSubmission.state == with_state)

        return query.first() and True or False

    def add_registration_window(self, start, end, **options):
        window = FormRegistrationWindow(
            start=start,
            end=end,
            **options
        )

        self.registration_windows.append(window)

        return window

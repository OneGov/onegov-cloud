from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.mixins import meta_property, content_property
from onegov.form.models.submission import FormSubmission
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

    def has_submissions(self, with_state=None):
        query = object_session(self).query(FormSubmission.id)
        query = query.filter(FormSubmission.name == self.name)

        if with_state is not None:
            query = query.filter(FormSubmission.state == with_state)

        return query.first() and True or False

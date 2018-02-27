from copy import deepcopy
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins.content import dictionary_based_property_factory
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


meta_local_property = dictionary_based_property_factory('local')


class ArchivedResult(Base, ContentMixin, TimestampMixin,
                     DomainOfInfluenceMixin, TitleTranslationsMixin):

    """ Stores the result of an election or vote. """

    __tablename__ = 'archived_results'

    #: Identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The date of the election/vote
    date = Column(Date, nullable=False)

    #: The last change of the results election/vote
    last_modified = Column(UTCDateTime, nullable=True)

    #: The last change of election/vote
    last_result_change = Column(UTCDateTime, nullable=True)

    #: Type of the result
    type = Column(
        Enum(
            'election',
            'election_compound',
            'vote',
            name='type_of_result'
        ),
        nullable=False
    )

    #: Origin of the result
    schema = Column(Text, nullable=False)

    #: The name of the principal
    name = Column(Text, nullable=False)

    #: Total number of political entities
    total_entities = Column(Integer, nullable=True)

    #: Number of already counted political entitites
    counted_entities = Column(Integer, nullable=True)

    @property
    def progress(self):
        return (self.counted_entities or 0, self.total_entities or 0)

    #: The link to the detailed results
    url = Column(Text, nullable=False)

    #: Title of the election
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

    def title_prefix(self, request):
        if self.is_fetched(request) and self.domain == 'municipality':
            return self.name

        return ''

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: The id of the election/vote.
    external_id = meta_property('id')

    #: The names of the elected candidates.
    elected_candidates = meta_property('elected_candidates', default=list)

    #: The URLs of the elections (if it is a compound)
    elections = meta_property('elections', default=list)

    #: The answer of a vote (accepted, rejected, counter-proposal).
    answer = meta_property('answer', default='')

    #: The nays rate of a vote.
    nays_percentage = meta_property('nays_percentage', default=100.0)

    #: The yeas rate of a vote.
    yeas_percentage = meta_property('yeas_percentage', default=0.0)

    #: True, if the vote or election has been counted.
    counted = meta_property('counted', default=False)

    #: True, if the vote or election has been completed.
    completed = meta_property('completed', default=False)

    #: The local results (municipal results if fetched from cantonal instance)
    local = meta_property('local')

    #: The answer if this a fetched cantonal/federal result on a communal
    #: instance.
    local_answer = meta_local_property('answer', '')

    #: The nays rate if this a fetched cantonal/federal result on a communal
    #: instance.
    local_nays_percentage = meta_local_property('nays_percentage', 100.0)

    #: The yeas rate if this a fetched cantonal/federal result on a communal
    #: instance.
    local_yeas_percentage = meta_local_property('yeas_percentage', 0.0)

    def is_fetched(self, request):
        """ Returns True, if this results has been fetched from another
        instance.

        """
        return self.schema != request.app.schema

    def is_fetched_by_municipality(self, request):
        """ Returns True, if this results has been fetched from another
        instance by a communal instance.

        """
        return (
            self.is_fetched(request) and
            request.app.principal.domain == 'municipality'
        )

    def display_answer(self, request):
        """ Returns the answer (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_answer
        return self.answer

    def display_nays_percentage(self, request):
        """ Returns the nays rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_nays_percentage
        return self.nays_percentage

    def display_yeas_percentage(self, request):
        """ Returns the yeas rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_yeas_percentage
        return self.yeas_percentage

    def copy_from(self, source):
        self.date = source.date
        self.last_modified = source.last_modified
        self.last_result_change = source.last_result_change
        self.type = source.type
        self.schema = source.schema
        self.name = source.name
        self.total_entities = source.total_entities
        self.counted_entities = source.counted_entities
        self.url = source.url
        self.title_translations = deepcopy(dict(source.title_translations))
        self.shortcode = source.shortcode
        self.domain = source.domain
        self.meta = deepcopy(dict(source.meta))

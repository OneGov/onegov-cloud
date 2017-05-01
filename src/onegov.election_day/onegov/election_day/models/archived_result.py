from copy import deepcopy
from onegov.ballot.models.common import DomainOfInfluenceMixin, MetaMixin
from onegov.core.orm import Base, translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE, UUID
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import Column, Date, Enum, Integer, Text
from uuid import uuid4


class ArchivedResult(Base, DomainOfInfluenceMixin, MetaMixin, TimestampMixin):

    """ Stores the result of an election or vote. """

    __tablename__ = 'archived_results'

    #: Identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: Identifies the date of the vote
    date = Column(Date, nullable=False)

    #: Identifies the date of the vote
    last_result_change = Column(UTCDateTime, nullable=False)

    #: Type of the result
    type = Column(
        Enum(
            'election',
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

    @property
    def title_prefix(self):
        if self.is_fetched and self.domain == 'municipality':
            return self.name

        return ''

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    @property
    def is_fetched(self):
        """ Returns True, if this results has been fetched from another
        instance.

        """
        return self.schema != self.session_manager.current_schema

    def is_fetched_by_municipality(self, request):
        """ Returns True, if this results has been fetched from another
        instance by a communal instance.

        """
        return (
            self.is_fetched and request.app.principal.domain == 'municipality'
        )

    def ensure_meta(self):
        """ Ensure that the meta dict is set. """

        if self.meta is None:
            self.meta = {}

    def ensure_meta_local(self):
        """ Ensure that the meta dict is set and contains the 'local' key. """

        self.ensure_meta()
        if 'local' not in self.meta:
            self.meta['local'] = {}

    @property
    def elected_candidates(self):
        """ The names of the elected candidates. """

        return (self.meta or {}).get('elected_candidates', [])

    @elected_candidates.setter
    def elected_candidates(self, value):
        self.ensure_meta()
        self.meta['elected_candidates'] = value

    @property
    def answer(self):
        """ The answer of a vote (accepted, rejected, counter-proposal). """

        return (self.meta or {}).get('answer', '')

    @answer.setter
    def answer(self, value):
        self.ensure_meta()
        self.meta['answer'] = value

    @property
    def local_answer(self):
        """ The answer if this a fetched cantonal/federal result on a communal
        instance.

        """

        return (self.meta or {}).get('local', {}).get('answer', '')

    @local_answer.setter
    def local_answer(self, value):
        self.ensure_meta_local()
        self.meta['local']['answer'] = value

    def display_answer(self, request):
        """ Returns the answer (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_answer
        return self.answer

    @property
    def nays_percentage(self):
        """ The nays rate of a vote. """

        return (self.meta or {}).get('nays_percentage', 100.0)

    @nays_percentage.setter
    def nays_percentage(self, value):
        self.ensure_meta()
        self.meta['nays_percentage'] = value

    @property
    def local_nays_percentage(self):
        """ The nays rate if this a fetched cantonal/federal result on a
        communal instance.

        """

        return (self.meta or {}).get('local', {}).get('nays_percentage', 100.0)

    @local_nays_percentage.setter
    def local_nays_percentage(self, value):
        self.ensure_meta_local()
        self.meta['local']['nays_percentage'] = value

    def display_nays_percentage(self, request):
        """ Returns the nays rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_nays_percentage
        return self.nays_percentage

    @property
    def yeas_percentage(self):
        """ The yeas rate of a vote. """

        return (self.meta or {}).get('yeas_percentage', 0.0)

    @yeas_percentage.setter
    def yeas_percentage(self, value):
        self.ensure_meta()
        self.meta['yeas_percentage'] = value

    @property
    def local_yeas_percentage(self):
        """ The yeas rate if this a fetched cantonal/federal result on a
        communal instance.

        """

        return (self.meta or {}).get('local', {}).get('yeas_percentage', 0.0)

    @local_yeas_percentage.setter
    def local_yeas_percentage(self, value):
        self.ensure_meta_local()
        self.meta['local']['yeas_percentage'] = value

    def display_yeas_percentage(self, request):
        """ Returns the yeas rate (depending on the current instance). """

        if self.is_fetched_by_municipality(request):
            return self.local_yeas_percentage
        return self.yeas_percentage

    @property
    def counted(self):
        """ True, if the vote or election has been counted. """

        return (self.meta or {}).get('counted', False)

    @counted.setter
    def counted(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['counted'] = value

    @property
    def completed(self):
        """ True, if the vote or election has been completed. """

        return (self.meta or {}).get('completed', False)

    @completed.setter
    def completed(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['completed'] = value

    def copy_from(self, source):
        self.date = source.date
        self.last_result_change = source.last_result_change
        self.type = source.type
        self.schema = source.schema
        self.name = source.name
        self.total_entities = source.total_entities
        self.counted_entities = source.counted_entities
        self.url = source.url
        self.title_translations = deepcopy(dict(source.title_translations))
        self.title = source.title
        self.shortcode = source.shortcode
        self.domain = source.domain
        self.meta = deepcopy(dict(source.meta))

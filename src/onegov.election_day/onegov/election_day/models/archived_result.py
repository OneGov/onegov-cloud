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

    def title_prefix(self, request=None, session=None):
        assert request or session
        session = session or request.app.session()
        if self.schema != session.info['schema']:
            if self.domain == 'municipality':
                return self.name

        return ''

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    @property
    def answer(self):
        return (self.meta or {}).get('answer', '')

    @answer.setter
    def answer(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['answer'] = value

    @property
    def nays_percentage(self):
        return (self.meta or {}).get('nays_percentage', 0.0)

    @nays_percentage.setter
    def nays_percentage(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['nays_percentage'] = value

    @property
    def yeas_percentage(self):
        return (self.meta or {}).get('yeas_percentage', 0.0)

    @yeas_percentage.setter
    def yeas_percentage(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['yeas_percentage'] = value

    @property
    def counted(self):
        return (self.meta or {}).get('counted', False)

    @counted.setter
    def counted(self, value):
        if self.meta is None:
            self.meta = {}
        self.meta['counted'] = value

    def copy_from(self, source):
        self.date = source.date
        self.last_result_change = source.last_result_change
        self.type = source.type
        self.schema = source.schema
        self.name = source.name
        self.total_entities = source.total_entities
        self.counted_entities = source.counted_entities
        self.url = source.url
        self.title_translations = source.title_translations
        self.title = source.title
        self.shortcode = source.shortcode
        self.domain = source.domain
        self.meta = source.meta

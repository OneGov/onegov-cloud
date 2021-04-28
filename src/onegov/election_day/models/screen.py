from collections import OrderedDict
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class ScreenType:
    types = (
        'simple_vote',
        'complex_vote',
        'majorz_election',
        'proporz_election',
        'election_compound'
    )

    def __init__(self, type_):
        assert type_ in self.types
        self.type = type_

    @property
    def categories(self):
        if self.type == 'simple_vote':
            return ('generic', 'vote')
        if self.type == 'complex_vote':
            return ('generic', 'vote', 'complex_vote')
        if self.type == 'majorz_election':
            return ('generic', 'election')
        if self.type == 'proporz_election':
            return ('generic', 'election', 'proporz_election')
        return ('generic', 'election_compound')


class Screen(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'election_day_screens'

    #: Identifies the screen
    id = Column(Integer, primary_key=True)

    #: A unique number for the path
    number = Column(Integer, unique=True, nullable=False)

    #: The vote
    vote_id = Column(
        Text,
        ForeignKey(Vote.id, onupdate='CASCADE'), nullable=True
    )
    vote = relationship('Vote', backref='screens')

    #: The election
    election_id = Column(
        Text,
        ForeignKey(Election.id, onupdate='CASCADE'), nullable=True
    )
    election = relationship('Election', backref='screens')

    #: The election compound
    election_compound_id = Column(
        Text,
        ForeignKey(ElectionCompound.id, onupdate='CASCADE'), nullable=True
    )
    election_compound = relationship('ElectionCompound', backref='screens')

    #: The title
    description = Column(Text, nullable=True)

    #: The type
    type = Column(Text, nullable=False)

    #: The content of the screen
    structure = Column(Text, nullable=False)

    #: Additional CSS
    css = Column(Text, nullable=True)

    #: The group this screen belongs to, used for cycling
    group = Column(Text, nullable=True)

    #: The duration this screen is presented if cycling
    duration = Column(Integer, nullable=True)

    @property
    def model(self):
        if self.type in ('simple_vote', 'complex_vote'):
            return self.vote
        if self.type in ('majorz_election', 'proporz_election'):
            return self.election
        if self.type == 'election_compound':
            return self.election_compound
        raise NotImplementedError()

    @property
    def screen_type(self):
        return ScreenType(self.type)

    @property
    def last_modified(self):
        changes = [self.last_change, self.model.last_change]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def next(self):
        if self.group:
            session = object_session(self)
            query = session.query(Screen.number, Screen)
            query = query.filter_by(group=self.group).order_by(Screen.number)
            screens = OrderedDict(query.all())
            if len(screens) > 1:
                keys = tuple(screens.keys())
                index = (keys.index(self.number) + 1) % len(screens)
                return screens[keys[index]]
        return None

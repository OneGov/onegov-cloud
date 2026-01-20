from __future__ import annotations

from collections import OrderedDict
from onegov.election_day.models.election import Election
from onegov.election_day.models.election_compound import ElectionCompound
from onegov.election_day.models.election_compound import ElectionCompoundPart
from onegov.election_day.models.vote import Vote
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime


class ScreenType:
    types = (
        'simple_vote',
        'complex_vote',
        'majorz_election',
        'proporz_election',
        'election_compound',
        'election_compound_part'
    )

    def __init__(self, type_: str):
        assert type_ in self.types
        self.type = type_

    @property
    def categories(self) -> tuple[str, ...]:
        if self.type == 'simple_vote':
            return ('generic', 'vote')
        if self.type == 'complex_vote':
            return ('generic', 'vote', 'complex_vote')
        if self.type == 'majorz_election':
            return ('generic', 'election', 'majorz_election')
        if self.type == 'proporz_election':
            return ('generic', 'election', 'proporz_election')
        if self.type == 'election_compound':
            return ('generic', 'election_compound')
        if self.type == 'election_compound_part':
            return ('generic', 'election_compound')
        raise NotImplementedError()


class Screen(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'election_day_screens'

    #: Identifies the screen
    id: Column[int] = Column(Integer, primary_key=True)

    #: A unique number for the path
    number: Column[int] = Column(Integer, unique=True, nullable=False)

    #: The vote
    vote_id: Column[str | None] = Column(
        Text,
        ForeignKey(Vote.id, onupdate='CASCADE'), nullable=True
    )
    vote: relationship[Vote | None] = relationship(
        'Vote',
        back_populates='screens'
    )

    #: The election
    election_id: Column[str | None] = Column(
        Text,
        ForeignKey(Election.id, onupdate='CASCADE'), nullable=True
    )
    election: relationship[Election | None] = relationship(
        'Election',
        back_populates='screens'
    )

    #: The election compound
    election_compound_id: Column[str | None] = Column(
        Text,
        ForeignKey(ElectionCompound.id, onupdate='CASCADE'), nullable=True
    )
    election_compound: relationship[ElectionCompound | None] = relationship(
        'ElectionCompound',
        back_populates='screens'
    )

    #: The domain of the election compound part.
    domain: Column[str | None] = Column(Text, nullable=True)

    #: The domain segment of the election compound part.
    domain_segment: Column[str | None] = Column(Text, nullable=True)

    @property
    def election_compound_part(self) -> ElectionCompoundPart | None:
        if self.election_compound and self.domain and self.domain_segment:
            return ElectionCompoundPart(
                self.election_compound, self.domain, self.domain_segment
            )
        return None

    #: The title
    description: Column[str | None] = Column(Text, nullable=True)

    #: The type
    type: Column[str] = Column(Text, nullable=False)

    #: The content of the screen
    structure: Column[str] = Column(Text, nullable=False)

    #: Additional CSS
    css: Column[str | None] = Column(Text, nullable=True)

    #: The group this screen belongs to, used for cycling
    group: Column[str | None] = Column(Text, nullable=True)

    #: The duration this screen is presented if cycling
    duration: Column[int | None] = Column(Integer, nullable=True)

    @property
    def model(
        self
    ) -> Election | ElectionCompound | ElectionCompoundPart | Vote | None:
        if self.type in ('simple_vote', 'complex_vote'):
            return self.vote
        if self.type in ('majorz_election', 'proporz_election'):
            return self.election
        if self.type == 'election_compound':
            return self.election_compound
        if self.type == 'election_compound_part':
            return self.election_compound_part
        raise NotImplementedError()

    @property
    def screen_type(self) -> ScreenType:
        return ScreenType(self.type)

    @property
    def last_modified(self) -> datetime | None:
        model = self.model
        assert model is not None
        changes = [self.last_change, model.last_change]
        set_changes = [change for change in changes if change]
        return max(set_changes) if set_changes else None

    @property
    def next(self) -> Screen | None:
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

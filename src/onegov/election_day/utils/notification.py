from __future__ import annotations

from itertools import chain
from onegov.election_day.models.subscriber import Subscriber
from sqlalchemy import and_
from typing import NamedTuple

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Sequence
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import Vote
    from sqlalchemy.sql import ColumnElement
    from typing import Literal
    from typing import TypeAlias

    DomainSubset: TypeAlias = Literal['canton', 'municipality'] | None


class ModelGroup(NamedTuple):
    domain: DomainSubset
    domain_segment: str | None
    elections: Sequence[Election]
    election_compounds: Sequence[ElectionCompound]
    votes: Sequence[Vote]
    filter: ColumnElement[bool]


def segment_models(
    elections: Sequence[Election],
    election_compounds: Sequence[ElectionCompound],
    votes: Sequence[Vote]
) -> list[ModelGroup]:
    """ Group elections, compounds and votes by subscribable notification
    segmenation.

    """

    model_chain: Iterator[Election | ElectionCompound | Vote]
    model_chain = chain(elections, election_compounds, votes)
    models = tuple(model_chain)
    if not models:
        return []

    domains_and_segments: set[tuple[DomainSubset, str | None]]
    domains_and_segments = {
        (
            'municipality' if model.domain == 'municipality' else 'canton',
            getattr(model, 'domain_segment', None) or None
        )
        for model in models
    }

    def match_(
        model: Election | ElectionCompound | Vote,
        domain: DomainSubset,
        domain_segment: str | None
    ) -> bool:
        if domain != 'municipality':
            return model.domain != 'municipality'
        return (
            model.domain == 'municipality'
            and getattr(model, 'domain_segment', None) == domain_segment
        )

    result = [
        ModelGroup(
            domain=None,
            domain_segment=None,
            elections=elections,
            election_compounds=election_compounds,
            votes=votes,
            filter=Subscriber.domain.is_(None)
        )
    ]
    for domain, domain_segment in domains_and_segments:
        result.append(
            ModelGroup(
                domain=domain,
                domain_segment=domain_segment,
                elections=[
                    m for m in elections if match_(m, domain, domain_segment)
                ],
                election_compounds=[
                    m for m in election_compounds
                    if match_(m, domain, domain_segment)
                ],
                votes=[m for m in votes if match_(m, domain, domain_segment)],
                filter=and_(
                    Subscriber.domain == 'municipality',
                    Subscriber.domain_segment == domain_segment
                ) if domain == 'municipality'
                else Subscriber.domain != 'municipality',
            )
        )

    return result

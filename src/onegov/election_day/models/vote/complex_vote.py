from __future__ import annotations

from onegov.election_day.models.vote.vote import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Ballot
    from onegov.election_day.models import BallotResult


class ComplexVote(Vote):
    """ A complex vote with proposal, counter-proposal and tie-breaker. """

    __mapper_args__ = {'polymorphic_identity': 'complex'}

    @property
    def counter_proposal(self) -> Ballot:
        return self.ballot('counter-proposal')

    @property
    def tie_breaker(self) -> Ballot:
        return self.ballot('tie-breaker')

    @staticmethod
    def get_answer(
        counted: bool,
        proposal: Ballot | BallotResult | None,
        counter_proposal: Ballot | BallotResult | None,
        tie_breaker: Ballot | BallotResult | None
    ) -> str | None:

        if not (counted and proposal and counter_proposal and tie_breaker):
            return None

        if proposal.accepted and counter_proposal.accepted:
            if tie_breaker.accepted:
                return 'proposal'
            else:
                return 'counter-proposal'

        elif proposal.accepted:
            return 'proposal'

        elif counter_proposal.accepted:
            return 'counter-proposal'

        else:
            return 'rejected'

    @property
    def answer(self) -> str | None:
        return self.get_answer(
            self.counted,
            self.proposal,
            self.counter_proposal,
            self.tie_breaker
        )

    @property
    def yeas_percentage(self) -> float:
        """ The percentage of yeas (discounts empty/invalid ballots).

        If the proposal won or both proposal and counter-proposal were
        rejected, we show the yeas/nays of the proposal.
        """

        if self.answer in ('proposal', 'rejected'):
            subject = self.proposal
        else:
            subject = self.counter_proposal

        return subject.yeas / ((subject.yeas + subject.nays) or 1) * 100

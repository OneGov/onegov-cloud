from onegov.ballot.models.vote.vote import Vote


class ComplexVote(Vote):
    """ A complex vote with proposal, counter-proposal and tie-breaker. """

    __mapper_args__ = {'polymorphic_identity': 'complex'}

    @property
    def polymorphic_base(self):
        return Vote

    @property
    def proposal(self):
        return self.ballot('proposal', create=True)

    @property
    def counter_proposal(self):
        return self.ballot('counter-proposal', create=True)

    @property
    def tie_breaker(self):
        return self.ballot('tie-breaker', create=True)

    @staticmethod
    def get_answer(counted, proposal, counter_proposal, tie_breaker):
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
    def answer(self):
        return self.get_answer(
            self.counted,
            self.proposal,
            self.counter_proposal,
            self.tie_breaker
        )

    @property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        if self.answer in ('proposal', 'rejected'):
            # if the proposal won or both proposal and counter-proposal
            # were rejected, we show the yeas/nays of the proposal
            subject = self.proposal
        else:
            subject = self.counter_proposal

        return subject.yeas / ((subject.yeas + subject.nays) or 1) * 100

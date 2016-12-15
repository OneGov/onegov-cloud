""" OneGov Ballot models the aggregated results of Swiss ballots and elections.
It takes hints from the eCH-0110 & eCH-0155 Standards.

See:

`eCH-0155: Datenstandard politische Rechte \
<http://www.ech.ch/vechweb/page?p=dossier&documentNumber=eCH-0155>`_
"""
from onegov.ballot.models.election import (
    Candidate,
    CandidateResult,
    Election,
    ElectionResult,
    List,
    ListConnection,
    ListResult,
    PanachageResult,
    PartyResult
)
from onegov.ballot.models.vote import Ballot, BallotResult, Vote
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

__all__ = [
    'Ballot',
    'BallotResult',
    'Candidate',
    'CandidateResult',
    'Election',
    'ElectionResult',
    'List',
    'ListConnection',
    'ListResult',
    'PanachageResult',
    'PartyResult',
    'Vote',
]


@listens_for(Ballot, 'mapper_configured')
@listens_for(Candidate, 'mapper_configured')
@listens_for(Election, 'mapper_configured')
@listens_for(List, 'mapper_configured')
@listens_for(ListConnection, 'mapper_configured')
@listens_for(Vote, 'mapper_configured')
def add_summarized_properties(mapper, cls):
    """ Takes the following attributes and adds them as hybrid_properties
    to the ballot. This results in a Ballot class that has all the following
    properties which will return the sum of the underlying results if called.

    E.g. this will return all the yeas of the joined ballot results::

        ballot.yeas

    """

    attributes = cls.summarized_properties

    def new_hybrid_property(attribute):

        @hybrid_property
        def sum_result(self):
            return self.aggregate_results(attribute)

        @sum_result.expression
        def sum_result(cls):
            return cls.aggregate_results_expression(cls, attribute)

        return sum_result

    for attribute in attributes:
        setattr(cls, attribute, new_hybrid_property(attribute))

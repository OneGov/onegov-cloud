from onegov.ballot import ComplexVote
from onegov.ballot import Vote


def add_last_modified_header(response, last_modified):
    """ Adds the give date to the response as Last-Modified header. """

    if last_modified:
        response.headers.add(
            'Last-Modified',
            last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        )


def add_cors_header(response):
    """ Adds a header allowing the response being used in scripts. """
    response.headers.add('Access-Control-Allow-Origin', '*')


def add_local_results(source, target, principal, session):
    """ Adds the result of the principal.

    Municipalities are interested in their own result rather than the
    cantonal end result of votes. We query the result of the municipality
    within the given vote (source) and add it to the target.

    """

    adjust = (
        principal.domain == 'municipality' and
        principal.id and
        source.type == 'vote' and
        source.external_id
    )
    if adjust:
        entity_id = principal.id
        vote = session.query(Vote).filter(Vote.id == source.external_id)
        vote = vote.first()
        if vote and vote.proposal:
            yeas = None
            nays = None
            answer = None

            proposal = vote.proposal.results
            proposal = proposal.filter_by(entity_id=entity_id)
            proposal = proposal.first()

            if proposal and proposal.counted:
                if vote.type == 'complex':
                    counter = vote.counter_proposal.results
                    counter = counter.filter_by(entity_id=entity_id)
                    counter = counter.first()

                    tie = vote.tie_breaker.results
                    tie = tie.filter_by(entity_id=entity_id)
                    tie = tie.first()

                    answer = ComplexVote.get_answer(
                        counter.counted,
                        proposal,
                        counter,
                        tie
                    )
                    if answer:
                        if answer == 'counter-proposal':
                            yeas = counter.yeas
                            nays = counter.nays
                        else:
                            yeas = proposal.yeas
                            nays = proposal.nays
                else:
                    yeas = proposal.yeas
                    nays = proposal.nays
                    answer = 'accepted' if proposal.accepted else 'rejected'

            if yeas and nays and answer:
                yeas = yeas / ((yeas + nays) or 1) * 100
                target.local_answer = answer
                target.local_yeas_percentage = yeas
                target.local_nays_percentage = 100 - yeas

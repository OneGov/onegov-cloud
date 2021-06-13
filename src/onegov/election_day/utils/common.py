from collections import OrderedDict

from onegov.ballot import ComplexVote
from onegov.ballot import Vote


def sublist_name_from_connection_id(conn_name, subconn_name):
    """
    Removes prefixed parent_connection_id from connection_id
    as introduced by sesam 2019.09
    :param conn_name: list connection name aka parent_connection_id
    :param subconn_name: subconnection name aka connection_id
    """
    return conn_name.replace(subconn_name, '', 1) or conn_name


class LastUpdatedOrderedDict(OrderedDict):
    """
    Stores items in the order the keys were last added.
    """

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().move_to_end(key)


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
        principal.domain == 'municipality'
        and principal.id
        and source.type == 'vote'
        and source.external_id
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


def get_parameter(request, name, type_, default):
    if type_ == int:
        try:
            return int(request.params.get(name))
        except Exception:
            return default

    if type_ == list:
        try:
            result = request.params[name].split(',')
            result = [item.strip() for item in result if item.strip()]
            return result if result else default
        except Exception:
            return default

    if type_ == bool:
        try:
            result = request.params[name].lower().strip()
            return result in ('true', '1') if result else default
        except Exception:
            return default

    raise NotImplementedError()

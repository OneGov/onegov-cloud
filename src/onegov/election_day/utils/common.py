from __future__ import annotations

from collections import OrderedDict
from onegov.core.utils import append_query_param
from onegov.election_day import _
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote
from urllib.parse import urlsplit
from urllib.parse import urlunsplit


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.election_day.models import ArchivedResult
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Election
    from onegov.election_day.models import Municipality
    from onegov.election_day.models import Notification
    from onegov.election_day.request import ElectionDayRequest
    from sqlalchemy.orm import DynamicMapped
    from sqlalchemy.orm import Session
    from typing import Protocol
    from webob.response import Response

    class HasNotifications(Protocol):
        notifications: DynamicMapped[Notification]


def sublist_name_from_connection_id(conn_name: str, subconn_name: str) -> str:
    """
    Removes prefixed parent_connection_id from connection_id as introduced by
    sesam 2019.09

    :param conn_name: list connection name aka parent_connection_id
    :param subconn_name: subconnection name aka connection_id
    """

    return conn_name.replace(subconn_name, '', 1) or conn_name


class LastUpdatedOrderedDict[KT, VT](OrderedDict[KT, VT]):
    """
    Stores items in the order the keys were last added.
    """

    def __setitem__(self, key: KT, value: VT) -> None:
        super().__setitem__(key, value)
        super().move_to_end(key)


def add_last_modified_header(
    response: Response,
    last_modified: datetime | None
) -> None:
    """ Adds the give date to the response as Last-Modified header. """

    if last_modified:
        response.headers.add(
            'Last-Modified',
            last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
        )


def add_cors_header(response: Response) -> None:
    """ Adds a header allowing the response being used in scripts. """
    response.headers.add('Access-Control-Allow-Origin', '*')


def add_local_results(
    source: ArchivedResult,
    target: ArchivedResult,
    principal: Canton | Municipality,
    session: Session
) -> None:
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
        query = session.query(Vote).filter(Vote.id == source.external_id)
        vote = query.first()
        if vote and vote.proposal:
            yeas = None
            nays = None
            answer = None

            proposal = None
            for result in vote.proposal.results:
                if str(result.entity_id) == entity_id:
                    proposal = result

            if proposal and proposal.counted:
                if isinstance(vote, ComplexVote):
                    counter_proposal = None
                    for result in vote.counter_proposal.results:
                        if str(result.entity_id) == entity_id:
                            counter_proposal = result
                    assert counter_proposal is not None

                    tie_breaker = None
                    for result in vote.tie_breaker.results:
                        if str(result.entity_id) == entity_id:
                            tie_breaker = result
                    assert tie_breaker is not None

                    answer = ComplexVote.get_answer(
                        counter_proposal.counted,
                        proposal,
                        counter_proposal,
                        tie_breaker
                    )
                    if answer:
                        if answer == 'counter-proposal':
                            yeas = counter_proposal.yeas
                            nays = counter_proposal.nays
                        else:
                            yeas = proposal.yeas
                            nays = proposal.nays
                else:
                    yeas = proposal.yeas
                    nays = proposal.nays
                    answer = 'accepted' if proposal.accepted else 'rejected'

            if yeas and nays and answer:
                yeas_percentage = yeas / ((yeas + nays) or 1) * 100
                target.local_answer = answer
                target.local_yeas_percentage = yeas_percentage
                target.local_nays_percentage = 100 - yeas_percentage


def get_parameter[T, ParamT: (int, bool, list[Any])](
    request: ElectionDayRequest,
    name: str,
    type_: type[ParamT],
    default: T
) -> ParamT | T:

    if type_ is bool:
        try:
            result = request.params[name].lower().strip()  # type:ignore
            return result in ('true', '1') if result else default  # type: ignore[return-value]
        except Exception:
            return default

    elif type_ is int:
        try:
            return int(request.params.get(name))  # type:ignore
        except Exception:
            return default

    elif type_ is list:
        try:
            result = request.params[name].split(',')  # type:ignore
            result = [item.strip() for item in result if item.strip()]
            return result if result else default  # type: ignore[return-value]
        except Exception:
            return default

    raise NotImplementedError()


def get_entity_filter(
    request: ElectionDayRequest,
    item: Election,
    view: str,
    selected: str | None
) -> list[tuple[str, bool, str]]:

    url = request.link(item, view)
    result = sorted(
        (
            entity,
            entity == selected,
            append_query_param(url, 'entity', entity)
        )
        for result in item.results
        if (entity := result.name)
    )
    result.insert(0, (_('All'), not selected, url))
    return result


def replace_url(url: str, start: str | None) -> str:
    if not start:
        return url

    parts = list(urlsplit(url))
    for index, part in enumerate(urlsplit(start)):
        if part:
            parts[index] = part

    return urlunsplit(parts)

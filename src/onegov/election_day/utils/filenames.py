from __future__ import annotations

from hashlib import sha256
from onegov.election_day.models import Ballot
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime


def filename_prefix(item: object) -> str:
    if isinstance(item, Ballot):
        return 'ballot'
    if isinstance(item, Vote):  # includes ComplexVote
        return 'vote'
    if isinstance(item, Election):  # includes ProporzElection
        return 'election'
    if isinstance(item, (ElectionCompound, ElectionCompoundPart)):
        return 'elections'
    return item.__class__.__name__.lower()


def pdf_filename(
    item: Ballot | Vote | Election | ElectionCompound | ElectionCompoundPart,
    locale: str,
    last_modified: datetime | None = None
) -> str:
    """ Generates a filename from an election or vote:

    .. code-block:: plain

        ['election' or 'vote']-[hash of id].[timestamp].[locale].pdf

    """
    if last_modified is None:
        assert hasattr(item, 'last_modified')
        last_modified = item.last_modified
        assert last_modified is not None

    return '{}-{}.{}.{}.pdf'.format(
        filename_prefix(item),
        sha256(str(item.id).encode('utf-8')).hexdigest(),
        int(last_modified.timestamp()),
        locale
    )


def svg_filename(
    item: Ballot | Vote | Election | ElectionCompound | ElectionCompoundPart,
    type_: str | None,
    locale: str,
    last_modified: datetime | None = None
) -> str:
    """ Generates a filename from an election, ballot or vote:

    .. code-block:: plain

        ['election' or 'vote']-[hash of id].[type_].[timestamp].[locale].svg

    """
    if last_modified is None:
        if isinstance(item, Ballot):
            last_modified = item.vote.last_modified
        else:
            last_modified = item.last_modified
        assert last_modified is not None

    ts = int(last_modified.timestamp())
    name = filename_prefix(item)
    if isinstance(item, Ballot):
        hash = str(item.id)
    elif isinstance(item, ElectionCompoundPart):
        assert item.election_compound_id is not None
        hash = '{}-{}'.format(
            sha256(item.election_compound_id.encode('utf-8')).hexdigest(),
            item.segment.replace(' ', '-').lower()
        )
    else:
        hash = sha256(item.id.encode('utf-8')).hexdigest()

    return f'{name}-{hash}.{ts}.{type_}.{locale}.svg'

from hashlib import sha256
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import Vote


def pdf_filename(item, locale):
    """ Generates a filename from an election or vote:

        ['election' or 'vote']-[hash of id].[timestamp].[locale].pdf

    """
    return '{}-{}.{}.{}.pdf'.format(
        'election' if isinstance(item, Election) else 'vote',
        sha256(item.id.encode('utf-8')).hexdigest(),
        int(item.last_modified.timestamp()),
        locale
    )


def svg_filename(item, type_, locale=None):
    """ Generates a filename from an election, ballot or vote:

        ['election' or 'vote']-[hash of id].[type_].[timestamp].[locale].svg

    """

    if isinstance(item, Ballot):
        name = 'ballot'
        hash = str(item.id)
        ts = int(item.vote.last_modified.timestamp())
    elif isinstance(item, Vote):
        name = 'vote'
        hash = sha256(item.id.encode('utf-8')).hexdigest()
        ts = int(item.last_modified.timestamp())
    else:
        name = 'election'
        hash = sha256(item.id.encode('utf-8')).hexdigest()
        ts = int(item.last_modified.timestamp())

    return '{}-{}.{}.{}.{}.svg'.format(name, hash, ts, type_, locale or 'any')

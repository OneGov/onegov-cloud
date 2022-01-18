from hashlib import sha256
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote


def filename_prefix(item):
    if isinstance(item, Ballot):
        return 'ballot'
    if isinstance(item, Vote):  # includes ComplexVote
        return 'vote'
    if isinstance(item, Election):  # includes ProporzElection
        return 'election'
    if isinstance(item, ElectionCompound):
        return 'elections'
    return item.__class__.__name__.lower()


def pdf_filename(item, locale, last_modified=None):
    """ Generates a filename from an election or vote:

        ['election' or 'vote']-[hash of id].[timestamp].[locale].pdf

    """
    return '{}-{}.{}.{}.pdf'.format(
        filename_prefix(item),
        sha256(item.id.encode('utf-8')).hexdigest(),
        int((last_modified or item.last_modified).timestamp()),
        locale
    )


def svg_filename(item, type_, locale=None, last_modified=None):
    """ Generates a filename from an election, ballot or vote::

        ['election' or 'vote']-[hash of id].[type_].[timestamp].[locale].svg

    """

    name = filename_prefix(item)
    if isinstance(item, Ballot):
        hash = str(item.id)
        ts = int((last_modified or item.vote.last_modified).timestamp())
    else:
        hash = sha256(item.id.encode('utf-8')).hexdigest()
        ts = int((last_modified or item.last_modified).timestamp())

    return '{}-{}.{}.{}.{}.svg'.format(name, hash, ts, type_, locale or 'any')

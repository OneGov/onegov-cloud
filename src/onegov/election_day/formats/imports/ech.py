from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import load_xml
from onegov.election_day.formats.imports.vote import import_votes_ech
from xsdata_ech.e_ch_0252_1_0 import Delivery


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Vote
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from sqlalchemy.orm import Session


def import_ech(
    principal: 'Canton | Municipality',
    file: IO[bytes],
    session: 'Session'
) -> tuple[list[FileImportError], set['Vote']]:
    """ Tries to import the given eCH XML file.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A tuple consisting of a list with errors and a set with updated
        votes.

    """

    delivery, error = load_xml(file)
    if error:
        return [error], set()

    if isinstance(delivery, Delivery):
        if delivery.vote_base_delivery:
            return import_votes_ech(
                principal, delivery.vote_base_delivery, session
            )

    return [FileImportError(_('File not supported'))], set()

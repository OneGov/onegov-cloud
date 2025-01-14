from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import load_xml
from onegov.election_day.formats.imports.election import import_elections_ech
from onegov.election_day.formats.imports.vote import import_votes_ech
from xsdata_ech.e_ch_0252_1_0 import Delivery as DeliveryV1
from xsdata_ech.e_ch_0252_2_0 import Delivery as DeliveryV2


from typing import IO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.formats.imports.common import ECHImportResultType
    from sqlalchemy.orm import Session


def import_ech(
    principal: Canton | Municipality,
    file: IO[bytes],
    session: Session,
    default_locale: str
) -> ECHImportResultType:
    """ Tries to import the given eCH XML file.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A tuple consisting of a list with errors and a set with updated
        votes.

    """

    delivery, error = load_xml(file)
    if error:
        return [error], set(), set()

    if not isinstance(delivery, (DeliveryV1, DeliveryV2)):
        return [FileImportError(_('File not supported'))], set(), set()

    errors = []
    updated = set()
    deleted = set()

    def unwrap(result: ECHImportResultType) -> None:
        errors.extend(result[0])
        updated.update(result[1])
        deleted.update(result[2])

    unwrap(import_votes_ech(principal, delivery, session))
    if isinstance(delivery, DeliveryV2):
        unwrap(
            import_elections_ech(principal, delivery, session, default_locale)
        )

    return errors, updated, deleted

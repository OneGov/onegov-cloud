from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import load_xml
from onegov.election_day.formats.imports.vote import import_votes_ech_0252
from xsdata_ech.e_ch_0252_1_0 import Delivery as ECH0252Delivery


def import_ech(principal, file, session):
    """ Tries to import the given eCH XML file.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """

    delivery, error = load_xml(file)
    if error:
        return [error], []

    if isinstance(delivery, ECH0252Delivery):
        return import_votes_ech_0252(principal, delivery, session)

    return [FileImportError(_('File not supported'))],

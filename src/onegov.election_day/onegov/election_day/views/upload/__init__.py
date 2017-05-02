from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError


def unsupported_year_error(year):
    return FileImportError(
        _(
            "The year ${year} is not yet supported", mapping={'year': year}
        )
    )

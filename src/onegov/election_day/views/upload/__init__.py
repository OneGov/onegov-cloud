from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import FileImportError


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest


def unsupported_year_error(year: int) -> FileImportError:
    return FileImportError(
        _(
            'The year ${year} is not yet supported', mapping={'year': year}
        )
    )


def set_locale(request: ElectionDayRequest) -> None:
    """ Sets the locale of the request by the Accept-Language header. """

    locale = request.headers.get('Accept-Language') or 'en'
    locale = locale if locale in request.app.locales else 'en'
    request.locale = locale


def translate_errors(
    errors: dict[str, list[Any]],
    request: ElectionDayRequest
) -> None:

    """ Translates and interpolates the given error messages. """
    for key, values in errors.items():
        errors[key] = new_values = []
        for value in values:
            result = {
                'message': request.translate(getattr(value, 'error', value)),
            }
            if hasattr(value, 'filename'):
                result['filename'] = value.filename
            if hasattr(value, 'line'):
                result['line'] = value.line
            new_values.append(result)

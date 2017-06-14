from onegov.election_day import _
from onegov.election_day.formats.common import FileImportError


def unsupported_year_error(year):
    return FileImportError(
        _(
            "The year ${year} is not yet supported", mapping={'year': year}
        )
    )


def set_locale(request):
    """ Sets the locale of the request by the Accept-Language header. """

    locale = request.headers.get('Accept-Language') or 'en'
    locale = locale if locale in request.app.locales else 'en'
    request.locale = locale


def translate_errors(errors, request):
    """ Translates and interpolates the given error messages. """

    for key, values in errors.items():
        errors[key] = []
        for value in values:
            result = {
                'message': request.translate(getattr(value, 'error', value)),
            }
            if hasattr(value, 'filename'):
                result['filename'] = value.filename
            if hasattr(value, 'line'):
                result['line'] = value.line
            errors[key].append(result)

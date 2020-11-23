from inspect import getmembers

from wtforms.validators import DataRequired

from onegov.form.fields import UploadField
from onegov.form.validators import StrictOptional


def prepare_for_submission(
        form_class,
        for_change_request=False,
        force_simple=True,
):
    # force all upload fields to be simple, we do not support the more
    # complex add/keep/replace widget, which is hard to properly support
    # and is not super useful in submissions
    def is_upload(attribute):
        if not hasattr(attribute, 'field_class'):
            return None

        return issubclass(attribute.field_class, UploadField)

    for name, field in getmembers(form_class, predicate=is_upload):

        if force_simple:
            if 'render_kw' not in field.kwargs:
                field.kwargs['render_kw'] = {}

            field.kwargs['render_kw']['force_simple'] = True

        # Otherwise the user gets stuck when in form validation not
        # changing the file
        if for_change_request:
            validators = [StrictOptional()] + [
                v for v in field.kwargs['validators'] or []
                if not isinstance(v, DataRequired)
            ]
            field.kwargs['validators'] = validators

    return form_class


def get_fields(form_class, names_only=False, exclude=None):
    """ Takes an unbound form and returns the name of the fields """
    def is_field(attribute):
        if not hasattr(attribute, 'field_class'):
            return None
        return True

    for name, field in getmembers(form_class, predicate=is_field):
        if exclude and name in exclude:
            continue
        if names_only:
            yield name
        else:
            yield name, field

import logging
log = logging.getLogger('onegov.form')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.form')  # noqa

from onegov.form.collection import (
    FormCollection,
    FormSubmissionCollection,
    FormDefinitionCollection
)
from onegov.form.core import Form, with_options
from onegov.form.display import render_field
from onegov.form.models import (
    FormDefinition,
    FormSubmission,
    FormSubmissionFile,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.form.parser.core import parse_form

__all__ = [
    'Form',
    'FormCollection',
    'FormDefinitionCollection',
    'FormSubmissionCollection',
    'FormDefinition',
    'FormSubmission',
    'FormSubmissionFile',
    'PendingFormSubmission',
    'CompleteFormSubmission',
    'parse_form',
    'render_field',
    'with_options'
]

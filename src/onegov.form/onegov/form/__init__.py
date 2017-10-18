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
from onegov.form.core import (
    FieldDependency,
    Form,
    merge_forms,
    move_fields,
    with_options,
)
from onegov.form.display import render_field
from onegov.form.integration import FormApp
from onegov.form.models import (
    FormDefinition,
    FormFile,
    FormSubmission,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.form.parser import flatten_fieldsets
from onegov.form.parser import parse_form
from onegov.form.parser import parse_formcode
from onegov.form.parser import WTFormsClassBuilder
from onegov.form.utils import decimal_range

__all__ = [
    'CompleteFormSubmission',
    'decimal_range',
    'flatten_fieldsets',
    'FieldDependency',
    'Form',
    'FormApp',
    'FormCollection',
    'FormDefinition',
    'FormDefinitionCollection',
    'FormFile',
    'FormSubmission',
    'FormSubmissionCollection',
    'merge_forms',
    'move_fields',
    'parse_form',
    'parse_formcode',
    'PendingFormSubmission',
    'render_field',
    'with_options',
    'WTFormsClassBuilder',
]

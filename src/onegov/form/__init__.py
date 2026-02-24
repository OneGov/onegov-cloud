from __future__ import annotations

import logging
log = logging.getLogger('onegov.form')
log.addHandler(logging.NullHandler())

from onegov.form.i18n import _

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
)
from onegov.form.display import render_field
from onegov.form.extensions import FormExtension, Extendable
from onegov.form.integration import FormApp
from onegov.form.models import (
    FormDefinition,
    SurveyDefinition,
    FormFile,
    FormSubmission,
    SurveySubmission,
    FormRegistrationWindow,
    SurveySubmissionWindow,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.form.parser import find_field
from onegov.form.parser import flatten_fieldsets
from onegov.form.parser import parse_form
from onegov.form.parser import parse_formcode
from onegov.form.parser import WTFormsClassBuilder
from onegov.form.utils import decimal_range, as_internal_id

__all__ = (
    '_',
    'as_internal_id',
    'CompleteFormSubmission',
    'decimal_range',
    'find_field',
    'flatten_fieldsets',
    'Extendable',
    'FieldDependency',
    'Form',
    'FormApp',
    'FormCollection',
    'FormDefinition',
    'FormDefinitionCollection',
    'FormExtension',
    'FormFile',
    'FormRegistrationWindow',
    'FormSubmission',
    'FormSubmissionCollection',
    'log',
    'merge_forms',
    'move_fields',
    'parse_form',
    'parse_formcode',
    'PendingFormSubmission',
    'SurveyDefinition',
    'SurveySubmissionWindow',
    'SurveySubmission',
    'render_field',
    'WTFormsClassBuilder',
)

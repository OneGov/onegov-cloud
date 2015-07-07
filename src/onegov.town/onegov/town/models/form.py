from onegov.form.models import FormDefinition
from onegov.town.models.extensions import (
    HiddenFromPublicExtension, ContactExtension, PersonLinkExtension
)


class BuiltinFormDefinition(FormDefinition, HiddenFromPublicExtension,
                            ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}


class CustomFormDefinition(FormDefinition, HiddenFromPublicExtension,
                           ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

from onegov.form.models import FormDefinition
from onegov.town.models.extensions import (
    HiddenFromPublicExtension, ContactExtension, PersonLinkExtension
)


class BuiltinFormDefinition(FormDefinition, HiddenFromPublicExtension,
                            ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}

    es_type_name = 'builtin_forms'

    @property
    def es_public(self):
        return not self.is_hidden_from_public


class CustomFormDefinition(FormDefinition, HiddenFromPublicExtension,
                           ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    es_type_name = 'custom_forms'

    @property
    def es_public(self):
        return not self.is_hidden_from_public

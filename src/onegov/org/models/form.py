from onegov.form.models import FormDefinition
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import ContactExtension
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import HoneyPotExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.search import SearchableContent


class BuiltinFormDefinition(FormDefinition, AccessExtension,
                            ContactExtension, PersonLinkExtension,
                            CoordinatesExtension, SearchableContent,
                            HoneyPotExtension):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}

    es_type_name = 'builtin_forms'
    es_id = 'name'

    @property
    def extensions(self):
        return tuple(set(super().extensions + ['honeypot']))


class CustomFormDefinition(FormDefinition, AccessExtension,
                           ContactExtension, PersonLinkExtension,
                           CoordinatesExtension, SearchableContent,
                           HoneyPotExtension):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    es_type_name = 'custom_forms'
    es_id = 'name'
    default_extensions = ['honeypot']

    @property
    def extensions(self):
        return tuple(set(super().extensions + ['honeypot']))

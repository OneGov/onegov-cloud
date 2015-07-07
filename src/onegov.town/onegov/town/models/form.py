from onegov.form.models import FormDefinition
from onegov.town.models.mixins import (
    HiddenMetaMixin, ContactContentMixin, PeopleContentMixin
)


class BuiltinFormDefinition(FormDefinition, HiddenMetaMixin,
                            ContactContentMixin, PeopleContentMixin):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}


class CustomFormDefinition(FormDefinition, HiddenMetaMixin,
                           ContactContentMixin, PeopleContentMixin):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

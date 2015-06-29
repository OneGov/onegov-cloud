from onegov.form.models import FormDefinition
from onegov.town.models.mixins import HiddenMetaMixin


class BuiltinFormDefinition(FormDefinition, HiddenMetaMixin):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}


class CustomFormDefinition(FormDefinition, HiddenMetaMixin):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

from onegov.form.models import FormDefinition


class BuiltinFormDefinition(FormDefinition):
    __mapper_args__ = {'polymorphic_identity': 'builtin'}


class CustomFormDefinition(FormDefinition):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

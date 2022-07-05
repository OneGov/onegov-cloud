from cached_property import cached_property
from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin
from onegov.translator_directory.models.mutation import TranslatorMutation


class TranslatorMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'translator_mutation'
    }

    @classmethod
    def create(cls, ticket, request, change, changes):
        return super().create(ticket, request, change=change, changes=changes)

    @cached_property
    def applied_changes(self):
        changes = self.meta.get('changes', [])
        if changes:
            labels = TranslatorMutation(None, None, None).labels
            changes = [labels.get(change, change) for change in changes]
        return changes


class AccreditationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'translator_accreditation'
    }

    @classmethod
    def create(cls, ticket, request, change, changes):
        return super().create(ticket, request, change=change, changes=changes)

    @cached_property
    def applied_changes(self):
        changes = self.meta.get('changes', [])
        if changes:
            labels = TranslatorMutation(None, None, None).labels
            changes = [labels.get(change, change) for change in changes]
        return changes

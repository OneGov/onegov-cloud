from cached_property import cached_property
from onegov.core.elements import Link
from onegov.core.templates import render_macro
from onegov.core.utils import linkify
from onegov.org import _
from onegov.org.models.ticket import OrgTicketMixin
from onegov.org.models.ticket import TicketDeletionMixin
from onegov.ticket import Handler
from onegov.ticket import handlers
from onegov.ticket import Ticket
from onegov.translator_directory.layout import TranslatorLayout
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.mutation import TranslatorMutation
from onegov.translator_directory.models.translator import Translator


class TranslatorMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'TRN'}
    es_type_name = 'translator_tickets'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('TRN')
class TranslatorMutationHandler(Handler, TicketDeletionMixin):

    handler_title = _("Translator")
    code_title = _("Translators")

    @cached_property
    def translator(self):
        return self.session.query(Translator).filter_by(
            id=self.data['handler_data'].get('id')
        ).first()

    @cached_property
    def mutation(self):
        if self.translator:
            return TranslatorMutation(
                self.session, self.translator.id, self.ticket.id
            )

    @property
    def deleted(self):
        return self.translator is None

    @cached_property
    def email(self):
        return self.data['handler_data'].get('submitter_email', '')

    @cached_property
    def message(self):
        return self.data['handler_data'].get('submitter_message', '')

    @cached_property
    def proposed_changes(self):
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self):
        return self.data.get('state')

    @property
    def title(self):
        return self.translator.title

    @property
    def subtitle(self):
        return _("Mutation")

    @cached_property
    def group(self):
        return _("Translator")

    def get_summary(self, request):
        layout = TranslatorLayout(self.translator, request)
        changes = self.mutation.translated(request, self.proposed_changes)
        return render_macro(
            layout.macros['display_translator_mutation'],
            request,
            {
                'translator': self.translator,
                'message': linkify(self.message).replace('\n', '<br>'),
                'changes': changes,
                'layout': layout
            }
        )

    def get_links(self, request):
        if self.deleted:
            return []

        links = [
            Link(
                text=_("Edit translator"),
                url=request.return_here(
                    request.link(self.translator, 'edit')
                ),
                attrs={'class': 'edit-link'}
            )
        ]

        if self.proposed_changes and self.state is None:
            links.append(
                Link(
                    text=_("Apply proposed changes"),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )

        return links


class AccreditationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'AKK'}
    es_type_name = 'translator_accreditations'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('AKK')
class AccreditationHandler(Handler, TicketDeletionMixin):

    handler_title = _("Accreditation")
    code_title = _("Accreditations")

    # @cached_property
    # def translator(self):
    #     return self.session.query(Translator).filter_by(
    #         id=self.data['handler_data'].get('id')
    #     ).first()

    @cached_property
    def accreditation(self):
        return Accreditation(self.session, self.ticket.id)

    @property
    def deleted(self):
        return False

    @cached_property
    def email(self):
        return self.data['handler_data'].get('submitter_email', '')

    # @cached_property
    # def message(self):
    #     return self.data['handler_data'].get('submitter_message', '')

    # @cached_property
    # def proposed_changes(self):
    #     return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self):
        return self.data.get('state')

    @property
    def title(self):
        return _("Request Accreditation")

    @property
    def subtitle(self):
        return ""

    @cached_property
    def group(self):
        return _("Accreditation")

    def get_summary(self, request):
        return ""
        # layout = TranslatorLayout(self.translator, request)
        # changes = self.mutation.translated(request, self.proposed_changes)
        # return render_macro(
        #     layout.macros['display_translator_mutation'],
        #     request,
        #     {
        #         'translator': self.translator,
        #         'message': linkify(self.message).replace('\n', '<br>'),
        #         'changes': changes,
        #         'layout': layout
        #     }
        # )

    def get_links(self, request):
        if self.deleted:
            return []

        if self.state is None:
            # todo: edit link
            return [
                Link(
                    text=_("Accept accreditation"),
                    url=request.return_here(
                        request.link(self.accreditation, 'accept')
                    ),
                    attrs={'class': 'accept-link'},
                )
            ]

        return []

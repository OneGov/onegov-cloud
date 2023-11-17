from functools import cached_property
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.templates import render_macro
from onegov.core.utils import linkify
from onegov.org import _
from onegov.org.models.ticket import OrgTicketMixin
from onegov.ticket import Handler
from onegov.ticket import handlers
from onegov.ticket import Ticket
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.layout import AccreditationLayout
from onegov.translator_directory.layout import TranslatorLayout
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.mutation import TranslatorMutation
from onegov.translator_directory.models.translator import Translator


class TranslatorMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'TRN'}  # type:ignore
    es_type_name = 'translator_tickets'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('TRN')
class TranslatorMutationHandler(Handler):

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

    @property
    def ticket_deletable(self):
        # For now we don't support this because lot's of functionality
        # depends on data in translator tickets
        if self.deleted:
            return True
        return False

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
            ),
            Link(
                _("Mail templates"),
                url=request.link(
                    self.translator, name='mail-templates'
                ),
                attrs={'class': 'envelope'},
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
    __mapper_args__ = {'polymorphic_identity': 'AKK'}  # type:ignore
    es_type_name = 'translator_accreditations'

    def reference_group(self, request):
        return self.title


@handlers.registered_handler('AKK')
class AccreditationHandler(Handler):

    handler_title = _('Accreditation')
    code_title = _('Accreditations')

    @cached_property
    def translator(self):
        return self.session.query(Translator).filter_by(
            id=self.data['handler_data'].get('id')
        ).first()

    @cached_property
    def accreditation(self):
        return Accreditation(self.session, self.translator.id, self.ticket.id)

    @property
    def deleted(self):
        return self.translator is None

    @property
    def ticket_deletable(self):
        # For now we don't support this because lot's of functionality
        # depends on data in translator tickets
        if self.deleted:
            return True
        return False

    @cached_property
    def email(self):
        return self.data['handler_data'].get('submitter_email', '')

    @cached_property
    def state(self):
        return self.data.get('state')

    @property
    def title(self):
        return self.translator.title

    @property
    def subtitle(self):
        return _('Request Accreditation')

    @cached_property
    def group(self):
        return _('Accreditation')

    def get_summary(self, request):
        layout = AccreditationLayout(self.translator, request)
        return render_macro(
            layout.macros['display_accreditation'],
            request,
            {
                'translator': self.translator,
                'ticket_data': self.data['handler_data'],
                'layout': layout
            }
        )

    def get_links(self, request):
        if self.deleted:
            return []

        links = []
        advanced_links = []

        if self.state is None:
            links.append(
                Link(
                    text=_('Grant admission'),
                    url=request.return_here(
                        request.link(self.accreditation, 'grant')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )

        if self.translator:
            advanced_links.append(
                Link(
                    text=_('Edit translator'),
                    url=request.return_here(
                        request.link(self.translator, 'edit')
                    ),
                    attrs={'class': ('edit-link', 'border')}
                )
            )
            advanced_links.append(
                Link(
                    text=_('Edit documents'),
                    url=request.return_here(
                        request.class_link(
                            TranslatorDocumentCollection,
                            {
                                'translator_id': self.translator.id,
                            }
                        )
                    ),
                    attrs={'class': ('edit-link', 'border')}
                )
            )
            links.append(
                Link(
                    _("Mail templates"),
                    url=request.link(
                        self.translator, name='mail-templates'
                    ),
                    attrs={'class': 'envelope'},
                )
            )
            if self.state is None:
                advanced_links.append(
                    Link(
                        text=_('Refuse admission'),
                        url=request.return_here(
                            request.link(self.accreditation, 'refuse')
                        ),
                        attrs={'class': 'delete-link'},
                    )
                )

        if advanced_links:
            links.append(
                LinkGroup(
                    _('Advanced'),
                    links=advanced_links,
                    right_side=False
                )
            )

        return links

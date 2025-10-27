from __future__ import annotations


from onegov.translator_directory.models.time_report import TranslatorTimeReport

from functools import cached_property
from markupsafe import Markup, escape
from onegov.core.elements import Link, LinkGroup
from onegov.core.templates import render_macro
from onegov.core.utils import linkify
from onegov.org import _
from onegov.org.models.ticket import OrgTicketMixin
from onegov.ticket import Handler
from onegov.ticket import handlers
from onegov.ticket import Ticket
from onegov.core.elements import Intercooler
from onegov.translator_directory.collections.documents import (
    TranslatorDocumentCollection)
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.layout import AccreditationLayout
from onegov.translator_directory.layout import TranslatorLayout
from onegov.translator_directory.models.accreditation import Accreditation
from onegov.translator_directory.models.mutation import TranslatorMutation
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.constants import TRANSLATOR_FA_ICON
from onegov.translator_directory.utils import get_custom_text

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.translator_directory.request import TranslatorAppRequest


class TranslatorMutationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'TRN'}  # type:ignore

    def reference_group(self, request: OrgRequest) -> str:
        return self.title


@handlers.registered_handler('TRN')
class TranslatorMutationHandler(Handler):

    handler_title = _('Translator')
    code_title = _('Translators')

    @cached_property
    def translator(self) -> Translator | None:
        return self.session.query(Translator).filter_by(
            id=self.data['handler_data'].get('id')
        ).first()

    @cached_property
    def mutation(self) -> TranslatorMutation | None:
        if self.translator:
            return TranslatorMutation(
                self.session, self.translator.id, self.ticket.id
            )
        return None

    @property
    def deleted(self) -> bool:
        return self.translator is None

    @property
    def ticket_deletable(self) -> bool:
        # For now we don't support this because lots of functionality
        # depends on data in translator tickets
        if self.deleted:
            return True
        return False

    @cached_property
    def email(self) -> str:
        return self.data['handler_data'].get('submitter_email', '')

    @cached_property
    def message(self) -> str:
        return self.data['handler_data'].get('submitter_message', '')

    @cached_property
    def proposed_changes(self) -> dict[str, Any]:
        return self.data['handler_data'].get('proposed_changes', {})

    @cached_property
    def state(self) -> str | None:
        return self.data.get('state')

    @cached_property
    def uploaded_files(self) -> list[Any]:
        from onegov.file import File

        file_ids = self.data['handler_data'].get('file_ids', [])
        if not file_ids:
            return []
        return [
            self.session.query(File).filter_by(id=fid).first()
            for fid in file_ids
        ]

    @property
    def title(self) -> str:
        return self.translator.title if self.translator else '<Deleted>'

    @property
    def subtitle(self) -> str:
        return _('Mutation')

    @cached_property
    def group(self) -> str:
        return _('Translator')

    def get_summary(
        self,
        request: TranslatorAppRequest  # type:ignore[override]
    ) -> Markup:

        assert self.mutation is not None
        assert self.translator is not None
        layout = TranslatorLayout(self.translator, request)
        changes = self.mutation.translated(request, self.proposed_changes)
        return render_macro(
            layout.macros['display_translator_mutation'],
            request,
            {
                'translator': self.translator,
                'message': linkify(self.message).replace('\n', Markup('<br>')),
                'changes': changes,
                'layout': layout,
                'uploaded_files': self.uploaded_files,
            },
        )

    def get_links(  # type:ignore[override]
        self,
        request: TranslatorAppRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        if self.deleted:
            return []

        links: list[Link | LinkGroup] = [
            Link(
                text=_('Edit translator'),
                url=request.return_here(
                    request.link(self.translator, 'edit')
                ),
                attrs={'class': 'edit-link'}
            ),
            Link(
                _('Mail templates'),
                url=request.link(
                    self.translator, name='mail-templates'
                ),
                attrs={'class': 'envelope'},
            )
        ]

        if self.proposed_changes and self.state is None:
            links.append(
                Link(
                    text=_('Apply proposed changes'),
                    url=request.return_here(
                        request.link(self.mutation, 'apply')
                    ),
                    attrs={'class': 'accept-link'},
                )
            )

        return links


class TimeReportTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'TRP'}  # type:ignore
    es_type_name = 'translator_time_reports'

    def reference_group(self, request: OrgRequest) -> str:
        return self.title


@handlers.registered_handler('TRP')
class TimeReportHandler(Handler):

    handler_title = _('Time Report')
    code_title = _('Time Reports')

    @cached_property
    def translator(self) -> Translator | None:
        return (
            self.session.query(Translator)
            .filter_by(id=self.data['handler_data'].get('translator_id'))
            .first()
        )

    @cached_property
    def time_report(self) -> TranslatorTimeReport | None:
        time_report_id = self.data['handler_data'].get('time_report_id')
        if not time_report_id:
            return None
        return (
            self.session.query(TranslatorTimeReport)
            .filter_by(id=time_report_id)
            .first()
        )

    @property
    def deleted(self) -> bool:
        return self.translator is None

    @property
    def ticket_deletable(self) -> bool:
        if self.deleted:
            return True
        if self.time_report and self.time_report.status == 'confirmed':
            return True
        return False

    @cached_property
    def email(self) -> str:
        return self.data['handler_data'].get('submitter_email', '')

    @cached_property
    def state(self) -> str | None:
        return self.data.get('state')

    @property
    def title(self) -> str:
        return self.translator.title if self.translator else '<Deleted>'

    @property
    def subtitle(self) -> str:
        return _('Time Report')

    @cached_property
    def group(self) -> str:
        return _('Time Report')

    def get_summary(
        self, request: TranslatorAppRequest  # type:ignore[override]
    ) -> Markup:
        if not self.translator or not self.time_report:
            return Markup('')

        layout = TranslatorLayout(self.translator, request)
        report = self.time_report

        assignment_type_key = report.assignment_type
        assignment_type_translated = '-'
        if assignment_type_key and assignment_type_key in INTERPRETING_TYPES:
            assignment_type_translated = request.translate(
                INTERPRETING_TYPES[assignment_type_key]
            )

        assignment_date_formatted = escape(
            layout.format_date(report.assignment_date, 'date')
        )
        summary_parts = [
            "<dl class='field-display'>",
            f"<dt>{request.translate(_('Assignment Date'))}</dt>",
            f'<dd>{assignment_date_formatted}</dd>',
            f"<dt>{request.translate(_('Duration'))}</dt>",
            f'<dd>{report.duration} min</dd>',
            f"<dt>{request.translate(_('Type'))}</dt>",
            f'<dd>{escape(assignment_type_translated)}</dd>',
        ]

        if report.case_number:
            summary_parts.extend(
                [
                    f"<dt>{request.translate(_('Case Number'))}</dt>",
                    f'<dd>{escape(report.case_number)}</dd>',
                ]
            )

        summary_parts.extend(
            [
                f"<dt>{request.translate(_('Hourly Rate'))}</dt>",
                f'<dd>{layout.format_currency(report.hourly_rate)}</dd>',
                f"<dt>{request.translate(_('Surcharge'))}</dt>",
                f'<dd>{report.surcharge_percentage}%</dd>',
                f"<dt>{request.translate(_('Travel'))}</dt>",
                f'<dd>{layout.format_currency(report.travel_compensation)}'
                f'</dd>',
                f"<dt><strong>{request.translate(_('Total'))}</strong></dt>",
                f'<dd><strong>{layout.format_currency(report.total_compensation)}</strong></dd>',
                '</dl>',
            ]
        )

        return Markup(''.join(summary_parts))  # nosec: B704

    def get_links(  # type:ignore[override]
        self, request: TranslatorAppRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        if self.deleted:
            return []

        links: list[Link | LinkGroup] = []
        time_report_links = []

        if self.time_report:
            time_report_links.append(
                Link(
                    text=_('View Time Report'),
                    url=request.return_here(request.link(self.time_report)),
                    attrs={'class': 'time'},
                )
            )

        time_report_links.append(
            Link(
                text=_('View translator'),
                url=request.return_here(request.link(self.translator)),
                attrs={'class': TRANSLATOR_FA_ICON},
            )
        )

        if self.state is None:
            time_report_links.append(
                Link(
                    text=_('Accept time report'),
                    url=request.link(self.ticket, 'accept-time-report'),
                    attrs={'class': 'accept-link'},
                    traits=(
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.link(
                                self.translator if request.is_member
                                else self.ticket
                            )
                        )
                    ),
                )
            )

        if time_report_links:
            links.append(
                LinkGroup(
                    _('Time Report'),
                    links=time_report_links,
                    right_side=False
                )
            )

        return links


class AccreditationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'AKK'}  # type:ignore

    def reference_group(self, request: OrgRequest) -> str:
        return self.title


@handlers.registered_handler('AKK')
class AccreditationHandler(Handler):

    handler_title = _('Accreditation')
    code_title = _('Accreditations')

    @cached_property
    def translator(self) -> Translator | None:
        return self.session.query(Translator).filter_by(
            id=self.data['handler_data'].get('id')
        ).first()

    @cached_property
    def accreditation(self) -> Accreditation | None:
        if self.translator is None:
            return None
        return Accreditation(self.session, self.translator.id, self.ticket.id)

    @property
    def deleted(self) -> bool:
        return self.translator is None

    @property
    def ticket_deletable(self) -> bool:
        # For now we don't support this because lot's of functionality
        # depends on data in translator tickets
        if self.deleted:
            return True
        return False

    @cached_property
    def email(self) -> str:
        return self.data['handler_data'].get('submitter_email', '')

    @cached_property
    def state(self) -> str | None:
        return self.data.get('state')

    @property
    def title(self) -> str:
        return self.translator.title if self.translator else '<Deleted>'

    @property
    def subtitle(self) -> str:
        return _('Request Accreditation')

    @cached_property
    def group(self) -> str:
        return _('Accreditation')

    def get_summary(
        self,
        request: TranslatorAppRequest  # type:ignore[override]
    ) -> Markup:
        layout = AccreditationLayout(self.translator, request)

        locale = request.locale.split('_')[0] if request.locale else None
        locale = 'de' if locale == 'de' else 'en'

        agreement_text = get_custom_text(
            request, f'({locale}) Custom admission course agreement')

        return render_macro(
            layout.macros['display_accreditation'],
            request,
            {
                'translator': self.translator,
                'ticket_data': self.data['handler_data'],
                'layout': layout,
                'agreement_text': agreement_text
            }
        )

    def get_links(  # type:ignore[override]
        self,
        request: TranslatorAppRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        if self.deleted:
            return []

        links: list[Link | LinkGroup] = []
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
                    _('Mail templates'),
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

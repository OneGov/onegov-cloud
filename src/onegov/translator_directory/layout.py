from __future__ import annotations


from functools import cached_property
from datetime import datetime
from dateutil.relativedelta import relativedelta
from purl import URL
from urllib.parse import urlencode
import pytz

from onegov.translator_directory import _
from onegov.core.elements import Block, Link, LinkGroup, Confirm, Intercooler
from onegov.core.utils import linkify
from onegov.town6.layout import DefaultLayout as BaseLayout
from onegov.org.models import Organisation
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import (
    member_can_see, editor_can_see, translator_can_see,
    GENDERS, ADMISSIONS, PROFESSIONAL_GUILDS,
    INTERPRETING_TYPES, TIME_REPORT_INTERPRETING_TYPES)
from onegov.translator_directory.utils import (
    get_accountant_emails_for_finanzstelle,
)


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Iterable
    from decimal import Decimal
    from onegov.translator_directory.models.language import Language
    from onegov.translator_directory.models.time_report import (
        TranslatorTimeReport,
    )
    from markupsafe import Markup
    from onegov.translator_directory.models.translator import (
        AdmissionState, Gender, Translator)
    from onegov.translator_directory.request import TranslatorAppRequest


class DefaultLayout(BaseLayout):

    request: TranslatorAppRequest

    @staticmethod
    def linkify(text: str | None) -> Markup:  # type:ignore[override]
        return linkify(text)

    @staticmethod
    def format_languages(languages: Iterable[Language] | None) -> str:
        return ', '.join(sorted(lang.name for lang in languages or ()))

    def format_gender(self, gender: Gender) -> str:
        return self.request.translate(GENDERS[gender])

    @staticmethod
    def format_drive_distance(number: float | None) -> str:
        if not number:
            return ''
        return f'{number} km'

    def format_boolean(self, val: bool | None) -> str:
        assert isinstance(val, bool) or val is None
        return self.request.translate(_('Yes') if val else _('No'))

    def format_admission(self, val: AdmissionState) -> str:
        return self.request.translate(ADMISSIONS[val])

    def show(self, attribute_name: str) -> bool:
        """Some attributes on the translator are hidden for less privileged
        users"""
        if self.request.is_admin:
            return True
        if self.request.is_editor:
            return attribute_name in editor_can_see
        if self.request.is_member:
            return attribute_name in member_can_see
        if self.request.is_translator:
            return attribute_name in translator_can_see
        return False

    def color_class(self, count: int) -> str | None:
        """ Depending how rare a language is offered by translators,
        apply a color code using the returned css class
        """
        if count <= 5:
            return 'text-orange'
        return None

    def format_prof_guild(self, key: str) -> str:
        if key in PROFESSIONAL_GUILDS:
            return self.request.translate(PROFESSIONAL_GUILDS[key])
        return key

    def format_interpreting_type(self, key: str) -> str:
        if key in INTERPRETING_TYPES:
            return self.request.translate(INTERPRETING_TYPES[key])
        if key in TIME_REPORT_INTERPRETING_TYPES:
            return self.request.translate(TIME_REPORT_INTERPRETING_TYPES[key])
        return key

    @staticmethod
    def format_currency(amount: Decimal | float | None) -> str:
        """Format amount as Swiss Francs."""
        if amount is None:
            return 'CHF 0.00'
        return f'CHF {amount:.2f}'


class TranslatorLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: Translator

        def __init__(
            self,
            model: Translator,
            request: TranslatorAppRequest
        ) -> None: ...

    def translator_data_outdated(self) -> bool:
        if self.request.is_translator:
            tz = pytz.timezone('Europe/Zurich')
            year_ago = datetime.now(tz=tz) - relativedelta(years=1)
            if self.model.modified:
                return self.model.modified < year_ago
            else:
                return self.model.created < year_ago
        else:
            return False

    @cached_property
    def file_collection(self) -> TranslatorDocumentCollection:
        return TranslatorDocumentCollection(
            self.request.session,
            translator_id=self.model.id,
            category=None
        )

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=(
                        Link(
                            text=_('Add translator'),
                            url=self.request.class_link(
                                TranslatorCollection, name='new'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    )
                ),
                Link(
                    text=_('Edit'),
                    url=self.request.link(
                        self.model, name='edit'
                    ),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    _('Delete'),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete '
                              'this translator?'),
                            _('This cannot be undone.'),
                            _('Delete translator'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                TranslatorCollection
                            )
                        )
                    )
                ),
                Link(
                    _('Documents'),
                    self.request.link(self.file_collection),
                    attrs={'class': 'documents'}
                ),
                Link(
                    _('Mail templates'),
                    url=self.request.link(
                        self.model, name='mail-templates'
                    ),
                    attrs={'class': 'envelope'}
                ),
                Link(
                    _('Add Time Report'),
                    url=self.request.link(self.model, name='add-time-report'),
                    attrs={'class': 'plus'},
                ),
            ]
        elif self.request.is_editor:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(
                        self.model, name='edit-restricted'
                    ),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    _('Report change'),
                    self.request.link(self.model, name='report-change'),
                    attrs={'class': 'report-change'}
                ),
                Link(
                    _('Add Time Report'),
                    url=self.request.link(self.model, name='add-time-report'),
                    attrs={'class': 'plus'},
                ),
            ]
        elif self.request.is_member:
            return [
                Link(
                    _('Add Time Report'),
                    url=self.request.link(self.model, name='add-time-report'),
                    attrs={'class': 'plus'},
                ),
            ]
        elif self.translator_data_outdated():
            return [
                Link(
                    _('Report change'),
                    self.request.link(self.model, name='report-change'),
                    attrs={'class': 'report-change'}
                ),
                Link(
                    _('Confirm current data'),
                    self.request.link(self.model,
                                      name='confirm-current-data'),
                    attrs={'class': 'accept-link'}
                )
            ]
        elif self.request.is_translator:
            return [
                Link(
                    _('Report change'),
                    self.request.link(self.model, name='report-change'),
                    attrs={'class': 'report-change'}
                )
            ]
        return None

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        if self.request.is_translator:
            links.append(
                Link(
                    text=_('Personal Information'),
                    url=self.request.link(self.model)
                ),
            )
        else:
            links.append(
                Link(
                    text=_('Translators'),
                    url=self.request.class_link(TranslatorCollection)
                ),
            )
            links.append(
                Link(
                    text=self.model.title,
                    url=self.request.link(self.model)
                )
            )
        return links


class EditTranslatorLayout(TranslatorLayout):
    @cached_property
    def title(self) -> str:
        return _('Edit translator')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Edit')))
        return links


class ReportTranslatorChangesLayout(TranslatorLayout):
    @cached_property
    def title(self) -> str:
        return _('Report change')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Report change')))
        return links


class ApplyTranslatorChangesLayout(TranslatorLayout):
    @cached_property
    def title(self) -> str:
        return _('Report change')

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Apply proposed changes')))
        return links


class MailTemplatesLayout(TranslatorLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        return [
            *super().breadcrumbs,
            Link(
                text=_('Mail templates'),
                url=self.request.link(
                    self.model, name='mail-templates'
                )
            )
        ]


class TranslatorCollectionLayout(DefaultLayout):

    model: TranslatorCollection

    @cached_property
    def title(self) -> str:
        return _('Search for translators')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [  # type:ignore[misc]
            *super().breadcrumbs,
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            )
        ]

    @cached_property
    def export_link(self) -> str | None:
        """ Returns the export link with current filters included, or None """
        if not self.request.is_admin:
            return None

        params = self.request.GET.copy()

        # Remove pagination parameter, not needed for export
        params.pop('page', None)

        # Ensure sorting parameters in the link match the actual state of the
        # collection model, handling defaults correctly.
        if self.model.order_by != 'last_name':
            params['order_by'] = self.model.order_by
        else:
            # Remove order_by from params if it's the default
            params.pop('order_by', None)

        if self.model.order_desc:
            params['order_desc'] = 'true'
        else:
            # Remove order_desc from params if it's the default (False)
            params.pop('order_desc', None)

        base_export_link = self.request.class_link(
            TranslatorCollection, name='export'
        )
        return (
            f'{base_export_link}?{urlencode(params, doseq=True)}'
            if params else base_export_link
        )

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                LinkGroup(
                    _('Add'),
                    links=(
                        Link(
                            text=_('Add translator'),
                            url=self.request.class_link(
                                TranslatorCollection, name='new'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    )
                ),
                Link(
                    _('Mail to all translators'),
                    url=self.request.app.mailto_link,
                    attrs={'class': 'envelope'},
                )
            ]
        elif self.request.is_editor or self.request.is_member:
            return []
        return None


class AddTranslatorLayout(TranslatorCollectionLayout):

    @cached_property
    def title(self) -> str:
        return _('Add translator')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links

    @property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []


class TranslatorDocumentsLayout(DefaultLayout):

    def __init__(self, model: Any, request: TranslatorAppRequest) -> None:
        super().__init__(model, request)
        request.include('upload')
        request.include('prompt')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [  # type:ignore[misc]
            *super().breadcrumbs,
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            ),
            Link(
                text=self.model.translator.title,
                url=self.request.link(self.model.translator)
            ),
            Link(text=_('Documents'))
        ]

    @cached_property
    def upload_url(self) -> str:
        url = URL(self.request.link(self.model, name='upload'))
        url = url.query_param('category', self.model.category)
        return self.csrf_protected_url(url.as_string())

    def link_for(self, category: str) -> str:
        return self.request.class_link(
            self.model.__class__,
            {'translator_id': self.model.translator_id, 'category': category}
        )


class LanguageCollectionLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(Link(_('Languages')))
        return links

    @property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return [LinkGroup(
            _('Add'),
            links=(
                Link(
                    text=_('Add language'),
                    url=self.request.class_link(
                        LanguageCollection, name='new'
                    ),
                    attrs={'class': 'new-language'}
                ),
            )
        )] if self.request.is_admin else []


class LanguageLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(_('Languages'),
                 url=self.request.class_link(LanguageCollection))
        )
        return links


class EditLanguageLayout(LanguageLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(self.model.name))
        links.append(Link(_('Edit')))
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if self.request.is_admin:
            if not self.model.deletable:
                return [
                    Link(
                        _('Delete'),
                        self.csrf_protected_url(
                            self.request.link(self.model)
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Block(
                                _("This language is used and can't be "
                                  "deleted."),
                                no=_('Cancel')
                            ),
                        )
                    ),
                ]
            return [
                Link(
                    _('Delete'),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete '
                              'this language?'),
                            _('This cannot be undone.'),
                            _('Delete language'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                TranslatorCollection
                            )
                        )
                    )
                ),
            ]
        return []


class AddLanguageLayout(LanguageLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links

    @property
    def editbar_links(self) -> list[Link | LinkGroup]:
        return []


class AccreditationLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                text=_('Accreditation'),
                url=self.request.link(self.model.ticket)
            )
        )
        return links


class RequestAccreditationLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                text=_('Accreditation'),
                url=self.request.class_link(
                    Organisation, name='request-accreditation'
                )
            )
        )
        return links


class GrantAccreditationLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                text=_('Accreditation'),
                url=self.request.link(self.model.ticket)
            )
        )
        links.append(Link(_('Grant admission')))
        return links


class RefuseAccreditationLayout(DefaultLayout):

    @property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                text=_('Accreditation'),
                url=self.request.link(self.model.ticket)
            )
        )
        links.append(Link(_('Refuse admission')))
        return links


class TimeReportCollectionLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: TimeReportCollection

    @cached_property
    def title(self) -> str:
        return _('Time Reports')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(Link(_('Time Reports')))
        return links

    @cached_property
    def has_confirmed_reports(self) -> bool:
        """Check if there are any confirmed reports available."""
        from onegov.translator_directory.models.time_report import (
            TranslatorTimeReport,
        )

        return (
            self.model.session.query(TranslatorTimeReport)
            .filter(TranslatorTimeReport.status == 'confirmed')
            .count()
            > 0
        )


class TimeReportLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: TranslatorTimeReport

        def __init__(
            self, model: TranslatorTimeReport, request: TranslatorAppRequest
        ) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(
                text=_('Time Reports'),
                url=self.request.class_link(TimeReportCollection),
            )
        )
        links.append(Link(self.model.title))
        return links

    def can_delete(self) -> bool:
        if self.request.is_admin:
            return True

        if not self.request.current_user:
            return False

        try:
            accountant_emails = get_accountant_emails_for_finanzstelle(
                self.request, self.model.finanzstelle
            )
            return self.request.current_user.username in accountant_emails
        except ValueError:
            return False

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if self.can_delete():
            return [
                Link(
                    _('Delete'),
                    self.csrf_protected_url(self.request.link(self.model)),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete '
                                'this time report?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete time report'),
                            _('Cancel'),
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                TimeReportCollection
                            ),
                        ),
                    ),
                ),
            ]
        return []

from functools import cached_property
from markupsafe import Markup
from purl import URL

from onegov.translator_directory import _
from onegov.core.elements import Block, Link, LinkGroup, Confirm, Intercooler
from onegov.core.utils import linkify
from onegov.org.layout import DefaultLayout as BaseLayout
from onegov.org.models import Organisation
from onegov.translator_directory.collections.documents import (
    TranslatorDocumentCollection)
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory.constants import (
    member_can_see, editor_can_see, translator_can_see,
    GENDERS, ADMISSIONS, PROFESSIONAL_GUILDS, INTERPRETING_TYPES)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.translator_directory.models.language import Language
    from onegov.translator_directory.models.translator import (
        AdmissionState, Gender, Translator)
    from onegov.translator_directory.request import TranslatorAppRequest


class DefaultLayout(BaseLayout):

    request: 'TranslatorAppRequest'

    @staticmethod
    def linkify(text: str | None) -> Markup:  # type:ignore[override]
        # FIXME: linkify should output Markup, once it does we can
        #        remove this wrapper
        return Markup(linkify(text))  # noqa: MS001

    @staticmethod
    def format_languages(languages: 'Iterable[Language] | None') -> str:
        return ', '.join(sorted(lang.name for lang in languages or ()))

    def format_gender(self, gender: 'Gender') -> str:
        return self.request.translate(GENDERS[gender])

    @staticmethod
    def format_drive_distance(number: float | None) -> str:
        if not number:
            return ''
        return f'{number} km'

    def format_boolean(self, val: bool | None) -> str:
        assert isinstance(val, bool) or val is None
        return self.request.translate((_('Yes') if val else _('No')))

    def format_admission(self, val: 'AdmissionState') -> str:
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
        return key


class TranslatorLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: 'Translator'

        def __init__(
            self,
            model: Translator,
            request: TranslatorAppRequest
        ) -> None: ...

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
                            text=_("Add translator"),
                            url=self.request.class_link(
                                TranslatorCollection, name='new'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    )
                ),
                Link(
                    text=_("Edit"),
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
                            _("Do you really want to delete "
                              "this translator?"),
                            _("This cannot be undone."),
                            _("Delete translator"),
                            _("Cancel")
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
            ]
        elif self.request.is_editor:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(
                        self.model, name='edit-restricted'
                    ),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    _('Report change'),
                    self.request.link(self.model, name='report-change'),
                    attrs={'class': 'report-change'}
                )
            ]
        elif self.request.is_member:
            return [
                Link(
                    _('Report change'),
                    self.request.link(self.model, name='report-change'),
                    attrs={'class': 'report-change'}
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
        return super().breadcrumbs + [
            Link(
                text=_('Mail templates'),
                url=self.request.link(
                    self.model, name='mail-templates'
                )
            )
        ]


class TranslatorCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Search for translators')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return super().breadcrumbs + [  # type:ignore[operator]
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            )
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                LinkGroup(
                    _('Add'),
                    links=(
                        Link(
                            text=_("Add translator"),
                            url=self.request.class_link(
                                TranslatorCollection, name='new'
                            ),
                            attrs={'class': 'new-person'}
                        ),
                    )
                ),
                Link(
                    _('Export Excel'),
                    url=self.request.class_link(
                        TranslatorCollection, name='export'
                    ),
                    attrs={'class': 'export-link'},
                ),
                Link(
                    _("Mail to all translators"),
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

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return super().breadcrumbs + [  # type:ignore[operator]
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
                    text=_("Add language"),
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
                                no=_("Cancel")
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
                            _("Do you really want to delete "
                              "this language?"),
                            _("This cannot be undone."),
                            _("Delete language"),
                            _("Cancel")
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

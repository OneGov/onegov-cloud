from cached_property import cached_property
from purl import URL

from onegov.translator_directory import _
from onegov.core.elements import Block, Link, LinkGroup, Confirm, Intercooler
from onegov.core.utils import linkify
from onegov.org.layout import DefaultLayout as BaseLayout
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import member_can_see, \
    editor_can_see, GENDERS, ADMISSIONS, PROFESSIONAL_GUILDS, \
    INTERPRETING_TYPES


class DefaultLayout(BaseLayout):

    @staticmethod
    def linkify(text):
        return linkify(text)

    @staticmethod
    def format_languages(languages):
        return ', '.join(sorted((lang.name for lang in languages or [])))

    def format_gender(self, gender):
        return self.request.translate(GENDERS[gender])

    @staticmethod
    def format_drive_distance(number):
        if not number:
            return ''
        return f'{number} km'

    def format_boolean(self, val):
        assert isinstance(val, bool)
        return self.request.translate((_('Yes') if val else _('No')))

    def format_admission(self, val):
        return self.request.translate(ADMISSIONS[val])

    def show(self, attribute_name):
        """Some attributes on the translator are hidden for less privileged
        users"""
        if self.request.is_member:
            return attribute_name in member_can_see
        if self.request.is_editor:
            return attribute_name in editor_can_see
        return True

    def color_class(self, count):
        """ Depending how rare a language is offered by translators,
        apply a color code using the returned css class
        """
        if count <= 5:
            return 'text-orange'

    def format_prof_guild(self, key):
        return self.request.translate(PROFESSIONAL_GUILDS[key])

    def format_interpreting_type(self, key):
        return self.request.translate(INTERPRETING_TYPES[key])


class TranslatorLayout(DefaultLayout):

    @cached_property
    def file_collection(self):
        return TranslatorDocumentCollection(
            self.request.session,
            translator_id=self.model.id,
            category=None
        )

    @cached_property
    def editbar_links(self):
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
                    _('Voucher template'),
                    self.request.link(self.request.app.org, name='voucher'),
                    attrs={'class': 'create-excel'}
                ),
                Link(
                    _('Documents'),
                    self.request.link(self.file_collection),
                    attrs={'class': 'documents'}
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
                    _('Voucher template'),
                    self.request.link(self.request.app.org, name='voucher'),
                    attrs={'class': 'create-excel'}
                ),
            ]
        elif self.request.is_member:
            return [
                Link(
                    _('Voucher template'),
                    self.request.link(self.request.app.org, name='voucher'),
                    attrs={'class': 'create-excel'}
                )
            ]

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs + [
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            ),
            Link(text=self.model.title)
        ]

        return links


class EditTranslatorLayout(TranslatorLayout):
    @cached_property
    def title(self):
        return _('Edit translator')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Edit')))
        return links


class TranslatorCollectionLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Search for translators')

    @cached_property
    def breadcrumbs(self):
        return super().breadcrumbs + [
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            )
        ]

    @cached_property
    def editbar_links(self):
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
                        Link(
                            text=_("Add language"),
                            url=self.request.class_link(
                                LanguageCollection, name='new'
                            ),
                            attrs={'class': 'new-language'}
                        )
                    )
                ),
                Link(
                    _('Export Excel'),
                    url=self.request.class_link(
                        TranslatorCollection, name='export'
                    ),
                    attrs={'class': 'export-link'}
                ),
                Link(
                    _('Voucher template'),
                    self.request.link(self.request.app.org, name='voucher'),
                    attrs={'class': 'create-excel'}
                )
            ]
        elif self.request.is_editor or self.request.is_member:
            return [
                Link(
                    _('Voucher template'),
                    self.request.link(self.request.app.org, name='voucher'),
                    attrs={'class': 'create-excel'}
                )
            ]


class AddTranslatorLayout(TranslatorCollectionLayout):

    @cached_property
    def title(self):
        return _('Add translator')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links

    @property
    def editbar_links(self):
        return []


class TranslatorDocumentsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return super().breadcrumbs + [
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
    def upload_url(self):
        url = URL(self.request.link(self.model, name='upload'))
        url = url.query_param('category', self.model.category)
        return self.csrf_protected_url(url.as_string())

    def link_for(self, category):
        return self.request.class_link(
            self.model.__class__,
            {'translator_id': self.model.translator_id, 'category': category}
        )


class LanguageCollectionLayout(DefaultLayout):

    @property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Languages')))
        return links

    @property
    def editbar_links(self):
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
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Languages'),
                 url=self.request.class_link(LanguageCollection))
        )
        return links


class EditLanguageLayout(LanguageLayout):

    @property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(self.model.name))
        links.append(Link(_('Edit')))
        return links

    @cached_property
    def editbar_links(self):
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
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links

    @property
    def editbar_links(self):
        return []

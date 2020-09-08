from cached_property import cached_property
from onegov.translator_directory import _
from onegov.core.elements import Link, LinkGroup, Confirm, Intercooler
from onegov.core.utils import linkify
from onegov.org.layout import DefaultLayout as BaseLayout
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import GENDERS_DESC, \
    GENDERS, member_can_see, editor_can_see, ADMISSIONS_DESC, ADMISSIONS


class DefaultLayout(BaseLayout):

    @staticmethod
    def linkify(text):
        return linkify(text)

    @staticmethod
    def format_languages(languages):
        return ', '.join(sorted((lang.name for lang in languages or [])))

    def format_gender(self, gender):
        return self.request.translate(GENDERS_DESC[GENDERS.index(gender)])

    @staticmethod
    def format_drive_distance(number):
        if not number:
            return ''
        return f'{number} km'

    def format_boolean(self, val):
        assert isinstance(val, bool)
        return self.request.translate((_('Yes') if val else _('No')))

    def format_admission(self, val):
        return self.request.translate(ADMISSIONS_DESC[ADMISSIONS.index(val)])


class TranslatorLayout(DefaultLayout):

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
                )
            ]

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(
                text=_('Translators'),
                url=self.request.class_link(TranslatorCollection)
            )
        )
        return links

    def show(self, attribute_name):
        """Some attributes on the translator are hidden for less privileged
        users"""
        if self.request.is_member:
            return attribute_name in member_can_see
        if self.request.is_editor:
            return attribute_name in editor_can_see
        return True

    def format_gender(self, gender):
        return self.request.translate(GENDERS_DESC[GENDERS.index(gender)])

    @staticmethod
    def format_drive_distance(number):
        if not number:
            return ''
        return f'{number} km'

    @staticmethod
    def format_languages(languages):
        return ', '.join(sorted((lang.name for lang in languages or [])))

    def color_class(self, count):
        """ Depending how rare a language is offered by translators,
        apply a color code using the returned css class
        """
        if count <= 5:
            return 'text-orange'


class EditTranslatorLayout(TranslatorLayout):
    @cached_property
    def title(self):
        return _('Edit translator')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Edit')))
        return links


class AddTranslatorLayout(TranslatorLayout):

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


class TranslatorCollectionLayout(TranslatorLayout):

    @cached_property
    def title(self):
        return _('Search for translators')

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
                        TranslatorCollection, name='export'))
            ]


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

    @property
    def editbar_links(self):
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

from cached_property import cached_property

from onegov.core.elements import Link
from onegov.core.utils import linkify
from onegov.translator_directory import _
from onegov.org.layout import DefaultLayout as BaseLayout
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import member_can_see, \
    editor_can_see, GENDERS_DESC, GENDERS, Language


class DefaultLayout(BaseLayout):

    @staticmethod
    def linkify(text):
        return linkify(text)


class TranslatorLayout(DefaultLayout):

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
    def editbar_links(self):
        return [
            Link(
                text=_("Add translator"),
                url=self.request.class_link(
                    TranslatorCollection, name='new'
                ),
                attrs={'class': 'add-icon'}
            ),
        ]

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(Link(_('Add')))
        return links

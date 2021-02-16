from cached_property import cached_property
from onegov.town6 import _
from onegov.core.elements import Link
from onegov.core.static import StaticFile
from onegov.foundation6.integration import FoundationLayout
from onegov.town6.theme import user_options
from onegov.org.layout import Layout as OrgLayout, AdjacencyListMixin


# from onegov.org.layout import Layout as OrgLayout, AdjacencyListMixin, \
#     SettingsLayoutMixin, NewsLayoutMixin, EditorLayoutMixin, \
#     FormSubmissionLayoutMixin, FormCollectionLayoutMixin, \
#     PersonCollectionLayoutMixin, PersonLayoutMixin, TicketsLayoutMixin, \
#     TicketNoteLayoutMixin, TicketChatMessageLayoutMixin, ResourcesLayoutMixin, \
#     ResourceRecipientsFormLayoutMixin, ResourceLayoutMixin, \
#     AllocationRulesLayoutMixin, AllocationEditFormLayoutMixin, \
#     EventBaseLayoutMixin, OccurrencesLayoutMixin, OccurrenceLayoutMixin, \
#     EventLayoutMixin, NewsletterLayoutMixin, RecipientLayoutMixin, \
#     ImageSetCollectionLayoutMixin, ImageSetLayoutMixin, \
#     UserManagementLayoutMixin, UserLayoutMixin, ExportCollectionLayoutMixin, \
#     PaymentProviderLayoutMixin, PaymentCollectionLayoutMixin, \
#     MessageCollectionLayoutMixin, DirectoryCollectionLayoutMixin, \
#     DirectoryEntryBaseLayoutMixin, DirectoryEntryCollectionLayoutMixin, \
#     DirectoryEntryLayoutMixin, PublicationLayoutMixin, DashboardLayoutMixin
#
#
class Layout(OrgLayout, FoundationLayout):

    @property
    def primary_color(self):
        return self.org.theme_options.get(
            'primary-color-ui', user_options['primary-color-ui'])

    @cached_property
    def font_awesome_path(self):
        return self.request.link(StaticFile(
            'font-awesome5/css/all.min.css',
            version=self.app.version
        ))

    @cached_property
    def drilldown_back(self):
        back = self.request.translate(_("back"))
        return '<li class="js-drilldown-back">' \
               f'<a class="new-back">{back}</a></li>'

    @property
    def on_homepage(self):
        return self.request.url == self.homepage_url


class DefaultLayout(Layout):

    @cached_property
    def top_navigation(self):
        return tuple(
            (Link(r.title, self.request.link(r)), tuple(
                Link(c.title, self.request.link(c))
                for c in self.request.exclude_invisible(r.children)
            )) for r in self.root_pages
        )


class AdjacencyListLayout(DefaultLayout, AdjacencyListMixin):
    pass


# class SettingsLayout(DefaultLayout, SettingsLayoutMixin):
#     pass

#
# class NewsLayout(AdjacencyListLayout, NewsLayoutMixin):
#     pass
#
#
# class EditorLayout(AdjacencyListLayout, EditorLayoutMixin):
#
#     def __init__(self, model, request, site_title):
#         super().__init__(model, request)
#         self.site_title = site_title
#         self.include_editor()
#
#
# class FormEditorLayout(DefaultLayout):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.include_editor()
#         self.include_code_editor()
#
#
# class FormSubmissionLayout(DefaultLayout, FormSubmissionLayoutMixin):
#
#     def __init__(self, model, request, title=None):
#         super().__init__(model, request)
#         self.include_code_editor()
#         self.title = title or self.form.title
#
#
# class FormCollectionLayout(DefaultLayout, FormCollectionLayoutMixin):
#     pass
#
#
# class PersonCollectionLayout(DefaultLayout, PersonCollectionLayoutMixin):
#     pass
#
#
# class PersonLayout(DefaultLayout, PersonLayoutMixin):
#     pass
#
#
# class TicketLayout(DefaultLayout, TicketsLayoutMixin):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.request.include('timeline')
#
#
# class TicketNoteLayout(DefaultLayout, TicketNoteLayoutMixin):
#
#     def __init__(self, model, request, title, ticket=None):
#         super().__init__(model, request)
#         self.title = title
#         self.ticket = ticket or model
#
#
# class TicketChatMessageLayout(DefaultLayout, TicketChatMessageLayoutMixin):
#
#     def __init__(self, model, request, internal=False):
#         super().__init__(model, request)
#         self.internal = internal
#
#
# class ResourcesLayout(DefaultLayout, ResourcesLayoutMixin):
#     pass
#
#
# class ResourceRecipientsLayout(DefaultLayout, ResourcesLayoutMixin):
#     pass
#
#
# class ResourceRecipientsFormLayout(
#         DefaultLayout, ResourceRecipientsFormLayoutMixin):
#
#     def __init__(self, model, request, title):
#         super().__init__(model, request)
#         self.title = title
#
#
# class ResourceLayout(DefaultLayout, ResourceLayoutMixin):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#
#         self.request.include('fullcalendar')
#
#
# class ReservationLayout(ResourceLayout):
#     editbar_links = None
#
#
# class AllocationRulesLayout(ResourceLayout, AllocationRulesLayoutMixin):
#     pass

#
# class AllocationEditFormLayout(DefaultLayout, AllocationEditFormLayoutMixin):
#     """ Same as the resource layout, but with different editbar links, because
#     there's not really an allocation view, but there are allocation forms.
#
#     """
#     pass
#
#
# class EventBaseLayout(DefaultLayout, EventBaseLayoutMixin):
#     pass
#
#
# class OccurrencesLayout(EventBaseLayout, OccurrencesLayoutMixin):
#     pass
#
#
# class OccurrenceLayout(EventBaseLayout, OccurrenceLayoutMixin):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.request.include('monthly-view')
#
#
# class EventLayout(EventBaseLayout, EventLayoutMixin):
#     pass
#
#
# class NewsletterLayout(DefaultLayout, NewsletterLayoutMixin):
#     pass
#
#
# class RecipientLayout(DefaultLayout, RecipientLayoutMixin):
#     pass
#
#
# class ImageSetCollectionLayout(DefaultLayout, ImageSetCollectionLayoutMixin):
#     pass
#
#
# class ImageSetLayout(DefaultLayout, ImageSetLayoutMixin):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.request.include('photoswipe')
#
#
# class UserManagementLayout(DefaultLayout, UserManagementLayoutMixin):
#     pass
#
#
# class UserLayout(DefaultLayout, UserLayoutMixin):
#     pass
#
#
# class ExportCollectionLayout(DefaultLayout, ExportCollectionLayoutMixin):
#     pass
#
#
# class PaymentProviderLayout(DefaultLayout, PaymentProviderLayoutMixin):
#     pass
#
#
# class PaymentCollectionLayout(DefaultLayout, PaymentCollectionLayoutMixin):
#     pass
#
#
# class MessageCollectionLayout(DefaultLayout, MessageCollectionLayoutMixin):
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.request.include('timeline')
#
#
# class DirectoryCollectionLayout(DefaultLayout, DirectoryCollectionLayoutMixin):
#
#     def __init__(self, model, request):
#         super().__init__(model, request)
#         self.include_editor()
#         self.include_code_editor()
#         self.request.include('iconwidget')
#
#
# class DirectoryEntryBaseLayout(DefaultLayout, DirectoryEntryBaseLayoutMixin):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.request.include('photoswipe')
#         if self.directory.marker_color:
#             self.custom_body_attributes['data-default-marker-color']\
#                 = self.directory.marker_color
#
#         if self.directory.marker_icon:
#             self.custom_body_attributes['data-default-marker-icon']\
#                 = self.directory.marker_icon.encode('unicode-escape')[2:]
#
#
# class DirectoryEntryCollectionLayout(
#         DirectoryEntryBaseLayout, DirectoryEntryCollectionLayoutMixin):
#     pass
#
#
# class DirectoryEntryLayout(
#         DirectoryEntryBaseLayout, DirectoryEntryLayoutMixin):
#     pass
#
#
# class PublicationLayout(DefaultLayout, PublicationLayoutMixin):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.request.include('filedigest')
#
#
# class DashboardLayout(DefaultLayout, DashboardLayoutMixin):
#     pass

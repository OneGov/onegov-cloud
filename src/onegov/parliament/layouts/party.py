from __future__ import annotations

# from functools import cached_property
# from onegov.core.elements import Confirm
# from onegov.core.elements import Intercooler
# from onegov.core.elements import Link
# from onegov.core.elements import LinkGroup

# from onegov.parliament import _
# from onegov.parliament.collections import RISPartyCollection
# from onegov.parliament.layouts.default import DefaultLayout


# class RISPartyCollectionLayout(DefaultLayout):
#
#     @cached_property
#     def title(self) -> str:
#         return _('Parties')
#
#     @cached_property
#     def og_description(self) -> str:
#         return self.request.translate(self.title)
#
#     @cached_property
#     def breadcrumbs(self) -> list[Link]:
#         return [
#             Link(_('Homepage'), self.homepage_url),
#             Link(_('Settings'), self.ris_settings_url),
#             Link(self.title, self.request.link(self.model))
#         ]
#
#     @cached_property
#     def editbar_links(self) -> list[LinkGroup] | None:
#         if self.request.is_manager:
#             return [
#                 LinkGroup(
#                     title=_('Add'),
#                     links=[
#                         Link(
#                             text=_('Party'),
#                             url=self.request.link(self.model, 'new'),
#                             attrs={'class': 'new-party'}
#                         ),
#                     ]
#                 ),
#             ]
#         return None
#
#     @cached_property
#     def ris_settings_url(self) -> str:
#         return self.request.link(self.app.org, 'ris-settings')
#
#     def format_minutes(self, value: int | None) -> str:
#         if not value or value < 0:
#             return ''
#
#         hours = value // 60
#         minutes = value % 60
#
#         if hours and minutes:
#             return _(
#                 '${hours} hours ${minutes} minutes',
#                 mapping={'hours': hours, 'minutes': minutes}
#             )
#         if hours:
#             return _('${hours} hours', mapping={'hours': hours})
#         return _('${minutes} minutes', mapping={'minutes': minutes})


# class PartyLayout(DefaultLayout):
#
#     @cached_property
#     def collection(self) -> RISPartyCollection:
#         return RISPartyCollection(self.request.session)
#
#     @cached_property
#     def title(self) -> str:
#         return self.model.name
#
#     @cached_property
#     def og_description(self) -> str:
#         return self.request.translate(self.title)
#
#     @cached_property
#     def breadcrumbs(self) -> list[Link]:
#         return [
#             Link(_('Homepage'), self.homepage_url),
#             Link(_('Settings'), self.ris_settings_url),
#             Link(
#                 _('Parties'),
#                 self.request.link(self.collection)
#             ),
#             Link(self.title, self.request.link(self.model))
#         ]
#
#     @cached_property
#     def editbar_links(self) -> list[Link] | None:
#         if self.request.is_manager:
#             return [
#                 Link(
#                     text=_('Edit'),
#                     url=self.request.link(self.model, 'edit'),
#                     attrs={'class': 'edit-link'}
#                 ),
#                 Link(
#                     text=_('Delete'),
#                     url=self.csrf_protected_url(
#                         self.request.link(self.model)
#                     ),
#                     attrs={'class': 'delete-link'},
#                     traits=(
#                         Confirm(
#                             _('Do you really want to delete this party?'),
#                             _('This cannot be undone.'),
#                             _('Delete party'),
#                             _('Cancel')
#                         ),
#                         Intercooler(
#                             request_method='DELETE',
#                             redirect_after=self.request.link(
#                                 self.collection
#                             )
#                         )
#                     )
#                 )
#             ]
#         return None

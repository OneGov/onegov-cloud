from __future__ import annotations

# from functools import cached_property
# from onegov.parliament import _
# from onegov.town6.layout import DefaultLayout as BaseDefaultLayout


# class DefaultLayout(BaseDefaultLayout):
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

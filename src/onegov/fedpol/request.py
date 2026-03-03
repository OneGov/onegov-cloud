from __future__ import annotations

from onegov.town6.request import TownRequest


class FedpolRequest(TownRequest):

    def is_visible(self, model: object) -> bool:
        if not super().is_visible(model):
            return False

        if self.is_manager:
            return True

        locale = getattr(model, 'locale', None)
        if locale is None:
            return True

        return locale == self.locale

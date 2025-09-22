from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.core.elements import Confirm
from onegov.pas import _
from onegov.pas.layouts.default import DefaultLayout
from onegov.core.elements import Intercooler


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.collections import ImportLogCollection
    from onegov.pas.models import ImportLog


class ImportLogCollectionLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: ImportLogCollection

    @cached_property
    def title(self) -> str:
        return _('Import History')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def kub_token_configured(self) -> bool:
        return bool(
            getattr(self.request.app, 'kub_test_api_token', None) or
            getattr(self.request.app, 'kub_api_token', None)
        )

    @cached_property
    def trigger_import_link(self) -> Link | None:
        if not self.request.is_manager or not self.kub_token_configured:
            return None

        return Link(
            text=_('Trigger Manual Import'),
            url=self.csrf_protected_url(
                self.request.link(self.model, 'trigger-import')
            ),
            attrs={
                'class': 'button success large',
                'id': 'trigger-import-btn',
                'data-import-started-text': _('Import Started...')
            },
            traits=(
                Confirm(
                    _('Are you sure you want to trigger a manual import?'),
                    _('This will start a new KUB data import process.'),
                    _('Trigger Import'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=self.request.link(self.model)
                )
            )
        )

    @cached_property
    def last_import_log(self) -> ImportLog | None:
        from sqlalchemy.orm import load_only
        return (
            self.model.query()
            .options(load_only(self.model.model_class.created))
            .order_by(self.model.model_class.created.desc())
            .first()
        )

    @property
    def last_import_time(self) -> str | None:
        if log := self.last_import_log:
            return self.format_date(log.created, 'relative')
        return None


class ImportLogLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: ImportLog

    @cached_property
    def collection(self) -> ImportLogCollection:
        from onegov.pas.collections import ImportLogCollection
        return ImportLogCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return _('Import Log Details')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Import History'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]

from __future__ import annotations

from onegov.api.models import ApiEndpoint
from onegov.org.api import PaginatedCollection
from onegov.org.models.meeting import Meeting, MeetingCollection
from onegov.org.models.parliament import (
    RISCommission, RISCommissionCollection,
    RISParliamentarian, RISParliamentarianCollection,
    RISParliamentaryGroup, RISParliamentaryGroupCollection)
from onegov.org.models.political_business import (
    PoliticalBusiness, PoliticalBusinessCollection)
from onegov.town6 import _
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6 import TownApp
    from onegov.town6.request import TownRequest


class MeetingApiEndpoint(ApiEndpoint[Meeting, UUID]):
    app: TownApp
    request: TownRequest
    endpoint = 'meetings'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Meetings'))

    @property
    def collection(self) -> PaginatedCollection[Meeting, UUID]:
        return PaginatedCollection(
            self.request,
            MeetingCollection(self.session),
            Meeting,
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(self, item: Meeting) -> dict[str, Any]:
        return {
            'title': item.title,
            'start_datetime': (
                item.start_datetime.isoformat()
                if item.start_datetime else None
            ),
            'end_datetime': (
                item.end_datetime.isoformat()
                if item.end_datetime else None
            ),
            'address': str(item.address) if item.address else None,
            'description': str(item.description) if item.description else None,
            'audio_link': item.audio_link or None,
            'video_link': item.video_link or None,
        }

    def item_links(self, item: Meeting) -> dict[str, Any]:
        return {'html': item}


class PoliticalBusinessApiEndpoint(ApiEndpoint[PoliticalBusiness, UUID]):
    app: TownApp
    request: TownRequest
    endpoint = 'political_businesses'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Political Businesses'))

    @property
    def collection(self) -> PoliticalBusinessCollection:
        result = PoliticalBusinessCollection(
            self.request,
            page=self.page or 0,
        )
        result.batch_size = self.batch_size
        return result

    def item_data(self, item: PoliticalBusiness) -> dict[str, Any]:
        return {
            'title': item.title,
            'number': item.number,
            'political_business_type': item.political_business_type,
            'status': item.status,
            'entry_date': (
                item.entry_date.isoformat() if item.entry_date else None
            ),
            'display_name': item.display_name,
        }

    def item_links(self, item: PoliticalBusiness) -> dict[str, Any]:
        return {'html': item}


class ParliamentarianApiEndpoint(ApiEndpoint[RISParliamentarian, UUID]):
    app: TownApp
    request: TownRequest
    endpoint = 'parliamentarians'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Parliamentarians'))

    @property
    def collection(self) -> PaginatedCollection[RISParliamentarian, UUID]:
        return PaginatedCollection(
            self.request,
            RISParliamentarianCollection(self.session),
            RISParliamentarian,
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(self, item: RISParliamentarian) -> dict[str, Any]:
        return {
            'first_name': item.first_name,
            'last_name': item.last_name,
            'title': item.title,
            'party': item.party,
            'active': item.active,
        }

    def item_links(self, item: RISParliamentarian) -> dict[str, Any]:
        return {
            'html': item,
            'picture': item.picture,
        }


class CommissionApiEndpoint(ApiEndpoint[RISCommission, UUID]):
    app: TownApp
    request: TownRequest
    endpoint = 'commissions'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Commissions'))

    @property
    def collection(self) -> PaginatedCollection[RISCommission, UUID]:
        return PaginatedCollection(
            self.request,
            RISCommissionCollection(self.session),
            RISCommission,
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(self, item: RISCommission) -> dict[str, Any]:
        return {
            'name': item.name,
            'description': str(item.description) if item.description else None,
        }

    def item_links(self, item: RISCommission) -> dict[str, Any]:
        return {'html': item}


class ParliamentaryGroupApiEndpoint(ApiEndpoint[RISParliamentaryGroup, UUID]):
    app: TownApp
    request: TownRequest
    endpoint = 'parliamentary_groups'
    pk_type = UUID

    @property
    def title(self) -> str:
        return self.request.translate(_('Parliamentary groups'))

    @property
    def collection(self) -> PaginatedCollection[RISParliamentaryGroup, UUID]:
        return PaginatedCollection(
            self.request,
            RISParliamentaryGroupCollection(self.session),
            RISParliamentaryGroup,
            batch_size=self.batch_size,
            page=self.page or 0,
        )

    def item_data(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {
            'name': item.name,
            'description': str(item.description) if item.description else None,
        }

    def item_links(self, item: RISParliamentaryGroup) -> dict[str, Any]:
        return {'html': item}

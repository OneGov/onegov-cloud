from __future__ import annotations

from onegov.agency.collections.agencies import ExtendedAgencyCollection
from onegov.agency.collections.agencies import PaginatedAgencyCollection
from onegov.agency.collections.memberships import PaginatedMembershipCollection
from onegov.agency.collections.people import ExtendedPersonCollection


__all__ = (
    'ExtendedAgencyCollection',
    'ExtendedPersonCollection',
    'PaginatedAgencyCollection',
    'PaginatedMembershipCollection'
)

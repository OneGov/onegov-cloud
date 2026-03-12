"""Type definitions for JSON import data structures."""

from __future__ import annotations

import logging
from typing import Literal, TypedDict

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.log import OutputHandler


class EmailData(TypedDict):
    id: str
    label: str
    email: str
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class AddressData(TypedDict):
    formattedAddress: str
    id: str
    label: str
    isDefault: bool
    organisationName: str
    organisationNameAddOn1: str
    organisationNameAddOn2: str
    addressLine1: str
    addressLine2: str
    street: str
    houseNumber: str
    dwellingNumber: str
    postOfficeBox: str
    swissZipCode: str
    swissZipCodeAddOn: str
    swissZipCodeId: str
    foreignZipCode: str
    locality: str
    town: str
    countryIdISO2: str
    countryName: str
    thirdPartyId: str | None
    modified: str
    created: str


class PhoneNumberData(TypedDict):
    id: str
    label: str
    phoneNumber: str
    phoneCategory: int
    otherPhoneCategory: str | None
    phoneCategoryText: str
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class UrlData(TypedDict):
    id: str
    label: str
    url: str | None
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class OrganizationData(TypedDict):
    created: str
    description: str
    htmlUrl: str
    id: str
    isActive: bool
    memberCount: int
    modified: str
    name: str
    organizationTypeTitle: (
        Literal['Kommission', 'Fraktion', 'Kantonsrat', 'Sonstige'] | None
    )
    primaryEmail: None
    status: int
    thirdPartyId: str | None
    url: str


class OrganizationDataWithinMembership(TypedDict):
    created: str
    description: str
    htmlUrl: str
    id: str
    isActive: bool
    memberCount: int
    modified: str
    name: str
    organizationTypeTitle: (
        Literal['Kommission', 'Fraktion', 'Kantonsrat', 'Sonstige'] | None
    )
    primaryEmail: EmailData | None
    status: int
    thirdPartyId: str | None
    url: str
    organizationType: int
    primaryAddress: AddressData | None
    primaryPhoneNumber: PhoneNumberData | None
    primaryUrl: UrlData | None
    statusDisplay: str
    tags: list[str]
    type: str


class PersonData(TypedDict):
    created: str
    firstName: str
    fullName: str
    htmlUrl: str
    id: str
    isActive: bool
    modified: str
    officialName: str
    personTypeTitle: str | None
    primaryEmail: EmailData | None
    salutation: str
    tags: list[str]
    thirdPartyId: str
    title: str
    url: str
    username: str | None


class MembershipData(TypedDict):
    department: str
    description: str
    emailReceptionType: str
    end: str | bool | None
    id: str
    isDefault: bool
    organization: OrganizationDataWithinMembership
    person: PersonData
    primaryAddress: AddressData | None
    primaryEmail: EmailData | None
    primaryPhoneNumber: PhoneNumberData | None
    primaryUrl: UrlData | None
    email: EmailData | None
    phoneNumber: PhoneNumberData | None
    address: AddressData | None
    urlField: UrlData | None
    role: str
    start: str | bool | None
    text: str
    thirdPartyId: str | None
    type: str
    typedId: str
    url: str


class OutputLogHandler(logging.Handler):
    """Logging handler that forwards messages to an OutputHandler."""

    def __init__(self, output_handler: OutputHandler) -> None:
        super().__init__()
        self.output_handler = output_handler

    def emit(self, record: logging.LogRecord) -> None:
        """Format and send log record to the output handler."""
        try:
            message = self.format(record)
            self.output_handler.info(message)
        except Exception:  # nosec B110
            # Avoid recursion in case of logging errors
            pass

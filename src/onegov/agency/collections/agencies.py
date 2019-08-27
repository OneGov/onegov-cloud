from onegov.agency.models import ExtendedAgency
from onegov.people import AgencyCollection


class ExtendedAgencyCollection(AgencyCollection):

    __listclass__ = ExtendedAgency

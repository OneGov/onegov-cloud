from onegov.core.orm.mixins import meta_property
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.people import AgencyMembership


class ExtendedAgencyMembership(AgencyMembership, HiddenFromPublicExtension):
    """ An extended version of the standard membership from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_membership'

    @property
    def es_public(self):
        if self.agency:
            if getattr(self.agency, 'is_hidden_from_public', False):
                return False
        if self.person:
            if getattr(self.person, 'is_hidden_from_public', False):
                return False
        return not self.is_hidden_from_public

    #: The prefix character.
    prefix = meta_property()

    #: A note to the membership.
    note = meta_property()

    #: An addition to the membership.
    addition = meta_property()

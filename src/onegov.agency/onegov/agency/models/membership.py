from onegov.people import AgencyMembership
from onegov.core.orm.mixins import meta_property


class ExtendedAgencyMembership(AgencyMembership):
    """ An extended version of the standard membership from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_membership'

    #: The prefix character.
    prefix = meta_property()

    #: A note to the membership.
    note = meta_property()

    #: An addition to the membership.
    addition = meta_property()

from onegov.libres.models import Resource
from onegov.town.models.extensions import (
    HiddenFromPublicExtension, ContactExtension, PersonLinkExtension
)


class DaypassResource(Resource, HiddenFromPublicExtension,
                      ContactExtension, PersonLinkExtension):
    __mapper_args__ = {'polymorphic_identity': 'daypass'}

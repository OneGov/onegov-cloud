from onegov.core.orm.mixins import meta_property
from onegov.people import Person


class ExtendedPerson(Person):

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_person'

    academic_title = meta_property()
    profession = meta_property()
    political_party = meta_property()
    year = meta_property()
    direct_phone = meta_property()

    @property
    def address_html(self):
        return '<p>{}</p>'.format(
            '<br>'.join((self.address or '').splitlines())
        )

    @property
    def notes_html(self):
        return '<p>{}</p>'.format(
            '<br>'.join((self.notes or '').splitlines())
        )

    @property
    def memberships_by_agency(self):

        def sortkey(membership):
            return membership.agency.title

        return sorted(self.memberships, key=sortkey)

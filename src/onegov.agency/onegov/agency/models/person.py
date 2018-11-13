from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.people import Person


class ExtendedPerson(Person, HiddenFromPublicExtension):
    """ An extended version of the standard person from onegov.people. """

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_person'

    @property
    def es_public(self):
        return not self.is_hidden_from_public

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

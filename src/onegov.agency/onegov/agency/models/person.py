from onegov.people import Person


class ExtendedPerson(Person):

    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_person'

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

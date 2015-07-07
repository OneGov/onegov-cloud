from collections import OrderedDict
from onegov.core.utils import linkify
from onegov.form import with_options
from onegov.form.parser.core import WTFormsClassBuilder, FieldDependency
from onegov.people import Person, PersonCollection
from onegov.town import _
from sqlalchemy.orm import object_session
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.widgets import TextArea


def extend_form(form_class, request, extensions):
    for extension in extensions:
        form_class = extension(form_class, request)

    return form_class


class HiddenMetaMixin(object):
    """ Extends any class that has a meta dictionary field with the ability to
    hide it from the public.

    see :func:`onegov.core.security.rules.has_permission_not_logged_in`

    """

    @property
    def is_hidden_from_public(self):
        return self.meta.get('is_hidden_from_public', False)

    @is_hidden_from_public.setter
    def is_hidden_from_public(self, is_hidden):
        self.meta['is_hidden_from_public'] = is_hidden


class PeopleContentMixin(object):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    @property
    def people(self):
        if 'people' in self.content:
            people = OrderedDict(self.content['people'])

            if len(people):
                query = PersonCollection(object_session(self)).query()
                query = query.filter(Person.id.in_(people.keys()))
                query = query.order_by(Person.last_name, Person.first_name)

                result = query.all()

                for person in result:
                    person.context_specific_function = people[person.id.hex]

                return result

    def get_selectable_people(self, request):
        query = PersonCollection(request.app.session()).query()
        query = query.order_by(Person.first_name, Person.last_name)

        return query.all()

    def extend_form_with_people(self, form_class, request):

        assert hasattr(form_class, 'get_page')
        assert hasattr(form_class, 'set_page')

        class PeoplePageForm(form_class):

            def get_people_fields(self, with_function):
                for field_id, field in self._fields.items():

                    # XXX this is kind of implicitly set by the fieldset
                    if field_id.startswith('people_'):
                        if with_function or not field_id.endswith('_function'):
                            yield field_id, field

            def get_people_and_function(self):
                fields = self.get_people_fields(with_function=False)

                for field_id, field in fields:
                    if field.data is True:
                        person_id = field.id.hex
                        function = self._fields[field_id + '_function'].data

                        yield person_id, function

            def get_page(self, page):
                super(PeoplePageForm, self).get_page(page)
                page.content['people'] = list(self.get_people_and_function())

            def set_page(self, page):
                super(PeoplePageForm, self).set_page(page)

                fields = self.get_people_fields(with_function=False)
                people = dict(page.content.get('people', []))

                for field_id, field in fields:
                    if field.id.hex in people:
                        self._fields[field_id].data = True
                        self._fields[field_id + '_function'].data\
                            = people[field.id.hex]

        builder = WTFormsClassBuilder(PeoplePageForm)
        builder.set_current_fieldset(_("People"))

        for person in self.get_selectable_people(request):
            field_id = builder.add_field(
                field_class=BooleanField,
                label=person.title,
                required=False,
                id=person.id
            )
            builder.add_field(
                field_class=StringField,
                label=_("Function"),
                required=False,
                dependency=FieldDependency(field_id, 'y')
            )

        return builder.form_class


class ContactContentMixin(object):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    @property
    def contact(self):
        return self.content.get('contact')

    @property
    def contact_html(self):
        return self.content.get('contact_html')

    def extend_form_with_contact(self, form_class, request):

        assert hasattr(form_class, 'get_page')
        assert hasattr(form_class, 'set_page')

        class ContactPageForm(form_class):
            contact_address = TextAreaField(
                label=_(u"Address"),
                fieldset=_("Contact"),
                widget=with_options(TextArea, rows=5)
            )

            def get_page(self, page):
                super(ContactPageForm, self).get_page(page)
                page.content['contact'] = self.contact_address.data
                page.content['contact_html'] = linkify(
                    self.contact_address.data)

            def set_page(self, page):
                super(ContactPageForm, self).set_page(page)
                self.contact_address.data = page.content.get('contact', '')

        return ContactPageForm

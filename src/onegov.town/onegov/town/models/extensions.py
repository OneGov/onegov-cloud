from collections import OrderedDict
from onegov.core.utils import linkify
from onegov.form import with_options
from onegov.form.parser.core import WTFormsClassBuilder, FieldDependency
from onegov.people import Person, PersonCollection
from onegov.town import _
from sqlalchemy.orm import object_session
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.widgets import TextArea


class ContentExtension(object):
    """ Extends classes based on :class:`onegov.core.orm.mixins.ContentMixin`
    with custom data that is stored in either 'meta' or 'content'.

    """

    @property
    def content_extensions(self):
        """ Returns all base classes of the current class which themselves have
        ``ContentExtension`` as baseclass.

        """
        for cls in self.__class__.__bases__:
            if ContentExtension in cls.__bases__:
                yield cls

    def with_content_extensions(self, form_class, request):
        """ Takes the given form and request and extends the form with
        all content extensions in the order in which they occur in the base
        class list.

        In other words, extends the forms with all used extension-fields.

        """

        # the content is injected/updated using the following methods - this
        # is currently a best practice in the code, but not really something
        # we enforce using base classes or something like it.
        assert hasattr(form_class, 'update_model')
        assert hasattr(form_class, 'apply_model')

        for extension in self.content_extensions:
            form_class = extension.extend_form(self, form_class, request)

        return form_class

    def extend_form(self, form_class, request):
        """ Must be implemented by each ContentExtension. Takes the form
        class without extension and adds the required fields to it.

        """
        raise NotImplementedError


class HiddenFromPublicExtension(ContentExtension):
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

    def extend_form(self, form_class, request):

        class HiddenPageForm(form_class):
            is_hidden_from_public = BooleanField(_("Hide from the public"))

            def update_model(self, model):
                super(HiddenPageForm, self).update_model(model)
                model.is_hidden_from_public = self.is_hidden_from_public.data

            def apply_model(self, model):
                super(HiddenPageForm, self).apply_model(model)
                self.is_hidden_from_public.data = model.is_hidden_from_public

        return HiddenPageForm


class ContactExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    @property
    def contact(self):
        return self.content.get('contact')

    @contact.setter
    def contact(self, value):
        self.content['contact'] = value
        self.content['contact_html'] = linkify(value)

    @property
    def contact_html(self):
        return self.content.get('contact_html')

    def extend_form(self, form_class, request):

        assert hasattr(form_class, 'update_model')
        assert hasattr(form_class, 'apply_model')

        class ContactPageForm(form_class):
            contact_address = TextAreaField(
                label=_(u"Address"),
                fieldset=_("Contact"),
                widget=with_options(TextArea, rows=5)
            )

            def update_model(self, model):
                super(ContactPageForm, self).update_model(model)
                model.contact = self.contact_address.data

            def apply_model(self, model):
                super(ContactPageForm, self).apply_model(model)
                self.contact_address.data = model.content.get('contact', '')

        return ContactPageForm


class PersonLinkExtension(ContentExtension):
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
        query = query.order_by(Person.last_name, Person.first_name)

        return query.all()

    def extend_form(self, form_class, request):

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

            def update_model(self, model):
                super(PeoplePageForm, self).update_model(model)
                model.content['people'] = list(self.get_people_and_function())

            def apply_model(self, model):
                super(PeoplePageForm, self).apply_model(model)

                fields = self.get_people_fields(with_function=False)
                people = dict(model.content.get('people', []))

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

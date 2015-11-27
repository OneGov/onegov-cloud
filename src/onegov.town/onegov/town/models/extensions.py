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

    def with_content_extensions(self, form_class, request, extensions=None):
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

        for extension in extensions or self.content_extensions:
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
                super().update_model(model)
                model.is_hidden_from_public = self.is_hidden_from_public.data

            def apply_model(self, model):
                super().apply_model(model)
                self.is_hidden_from_public.data = model.is_hidden_from_public

        return HiddenPageForm


class VisibleOnHomepageExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    a boolean indicating if the page should be shown on the homepage or not.

    """

    @property
    def is_visible_on_homepage(self):
        return self.meta.get('is_visible_on_homepage', False)

    @is_visible_on_homepage.setter
    def is_visible_on_homepage(self, is_visible):
        if is_visible:
            self.meta['is_visible_on_homepage'] = True
        elif 'is_visible_on_homepage' in self.meta:
            del self.meta['is_visible_on_homepage']

    def extend_form(self, form_class, request):

        # do not show on root pages
        if self.parent_id is None:
            return form_class

        class VisibleOnHomepageForm(form_class):
            is_visible_on_homepage = BooleanField(_("Visible on homepage"))

            def update_model(self, model):
                super().update_model(model)
                model.is_visible_on_homepage = self.is_visible_on_homepage.data

            def apply_model(self, model):
                super().apply_model(model)
                self.is_visible_on_homepage.data = model.is_visible_on_homepage

        return VisibleOnHomepageForm


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

        if value:
            self.content['contact_html'] = '<ul><li>{}</li></ul>'.format(
                '</li><li>'.join(linkify(value).splitlines())
            )
        else:
            self.content['contact_html'] = ""

    @property
    def contact_html(self):
        return self.content.get('contact_html')

    def extend_form(self, form_class, request):

        assert hasattr(form_class, 'update_model')
        assert hasattr(form_class, 'apply_model')

        class ContactPageForm(form_class):
            contact_address = TextAreaField(
                label=_("Address"),
                fieldset=_("Contact"),
                widget=with_options(TextArea, rows=5)
            )

            def update_model(self, model):
                super().update_model(model)
                model.contact = self.contact_address.data

            def apply_model(self, model):
                super().apply_model(model)
                self.contact_address.data = model.content.get('contact', '')

        return ContactPageForm


class PersonLinkExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    @property
    def people(self):
        """ Returns the people linked to this content or None.

        The context specific function is temporarily stored on the
        ``context_specific_function`` attribute on each object in the
        resulting list.

        """

        if not self.content.get('people'):
            return None

        people = OrderedDict(self.content['people'])

        query = PersonCollection(object_session(self)).query()
        query = query.filter(Person.id.in_(people.keys()))

        result = []

        for person in query.all():
            person.context_specific_function = people[person.id.hex]
            result.append(person)

        order = list(people.keys())
        result.sort(key=lambda p: order.index(p.id.hex))

        return result

    def get_selectable_people(self, request):
        """ Returns a list of people which may be linked. """

        query = PersonCollection(request.app.session()).query()
        query = query.order_by(Person.last_name, Person.first_name)

        return query.all()

    def get_person_function_by_id(self, id):
        for _id, function in self.content.get('people', []):
            if id == _id:
                return function

    def move_person(self, subject, target, direction):
        """ Moves the subject below or above the target.

        :subject:
            The key of the person to be moved.

        :target:
            The key of the person above or below which the subject is moved.

        :direction:
            The direction relative to the target. Either 'above' or 'below'.

        """
        assert direction in ('above', 'below')
        assert subject != target
        assert self.content.get('people')

        def new_order():
            subject_function = self.get_person_function_by_id(subject)
            target_function = self.get_person_function_by_id(target)

            for person, function in self.content['people']:

                if person == subject:
                    continue

                if person == target and direction == 'above':
                    yield subject, subject_function
                    yield target, target_function
                    continue

                if person == target and direction == 'below':
                    yield target, target_function
                    yield subject, subject_function
                    continue

                yield person, function

        self.content['people'] = list(new_order())

    def extend_form(self, form_class, request):

        # XXX this is kind of implicitly set by the builder
        fieldset_id = 'people'
        fieldset_label = _("People")

        class PeoplePageForm(form_class):

            def get_people_fields(self, with_function):
                for field_id, field in self._fields.items():
                    if field_id.startswith(fieldset_id):
                        if with_function or not field_id.endswith('_function'):
                            yield field_id, field

            def get_people_and_function(self, selected_only=True):
                fields = self.get_people_fields(with_function=False)

                for field_id, field in fields:
                    if not selected_only or field.data is True:
                        person_id = field.id.hex
                        function = self._fields[field_id + '_function'].data

                        yield person_id, function

            def is_ordered_people(self, existing_people):
                """ Returns True if the current list of people is ordered
                from A to Z.

                """
                if not existing_people:
                    return True

                existing_people = OrderedDict(existing_people)
                ordered_people = OrderedDict(self.get_people_and_function(
                    selected_only=False
                ))

                sorted_existing_people = sorted(
                    [key for key in existing_people],
                    key=list(ordered_people.keys()).index
                )

                return list(existing_people.keys()) == sorted_existing_people

            def update_model(self, model):
                previous_people = model.content.get('people', [])

                super().update_model(model)

                if self.is_ordered_people(previous_people):
                    # if the people are ordered a-z, we take the ordering from
                    # get_people_and_function, which comes by A-Z already
                    model.content['people'] = list(
                        self.get_people_and_function()
                    )
                else:
                    # if the people are not ordered we keep the order of the
                    # existing list and add the new people at the end
                    existing = set()
                    selected = {
                        key for key, function
                        in self.get_people_and_function()
                    }

                    old_people = list()
                    new_people = list()

                    for id, function in previous_people:
                        if id in selected:
                            old_people.append((id, function))
                            existing.add(id)

                    for id, function in self.get_people_and_function():
                        if id not in existing:
                            new_people.append((id, function))

                    model.content['people'] = old_people + new_people

            def apply_model(self, model):
                super().apply_model(model)

                fields = self.get_people_fields(with_function=False)
                people = dict(model.content.get('people', []))

                for field_id, field in fields:
                    if field.id.hex in people:
                        self._fields[field_id].data = True
                        self._fields[field_id + '_function'].data\
                            = people[field.id.hex]

        builder = WTFormsClassBuilder(PeoplePageForm)
        builder.set_current_fieldset(fieldset_label)

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

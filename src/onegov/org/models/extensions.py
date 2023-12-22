from collections import OrderedDict

from onegov.core.orm.mixins import meta_property, content_property
from onegov.core.utils import normalize_for_url, to_html_ul
from onegov.form import FieldDependency, WTFormsClassBuilder
from onegov.gis import CoordinatesMixin
from onegov.org import _
from onegov.org.forms import ResourceForm
from onegov.org.forms.extensions import CoordinatesFormExtension
from onegov.org.forms.extensions import PublicationFormExtension
from onegov.org.forms.fields import UploadOrSelectExistingMultipleFilesField
from onegov.people import Person, PersonCollection
from onegov.reservation import Resource
from sedate import to_timezone, utcnow
from sqlalchemy.orm import object_session
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.form.types import _FormT
    from onegov.org.request import OrgRequest
    from typing import Protocol
    from wtforms import Field

    class SupportsExtendForm(Protocol):
        def extend_form(
            self,
            form_class: type[_FormT],
            request: OrgRequest
        ) -> type[_FormT]: ...


class ContentExtension:
    """ Extends classes based on :class:`onegov.core.orm.mixins.ContentMixin`
    with custom data that is stored in either 'meta' or 'content'.

    """

    @property
    def content_extensions(self) -> 'Iterator[type[ContentExtension]]':
        """ Returns all base classes of the current class which themselves have
        ``ContentExtension`` as baseclass.

        """
        for cls in self.__class__.__bases__:
            if ContentExtension in cls.__bases__:
                yield cls

    def with_content_extensions(
        self,
        form_class: type['_FormT'],
        request: 'OrgRequest',
        extensions: 'Iterable[type[SupportsExtendForm]] | None' = None
    ) -> type['_FormT']:
        """ Takes the given form and request and extends the form with
        all content extensions in the order in which they occur in the base
        class list.

        In other words, extends the forms with all used extension-fields.

        """

        disabled_extensions = request.app.settings.org.disabled_extensions
        for extension in extensions or self.content_extensions:
            if extension.__name__ not in disabled_extensions:
                form_class = extension.extend_form(self, form_class, request)

        return form_class

    def extend_form(
        self,
        form_class: type['_FormT'],
        request: 'OrgRequest'
    ) -> type['_FormT']:
        """ Must be implemented by each ContentExtension. Takes the form
        class without extension and adds the required fields to it.

        """
        raise NotImplementedError


class AccessExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    set one of the following access levels:

    * 'public' - The default, the model is listed and accessible.
    * 'private' - Neither listed nor accessible, except administrators
                  and editors.
    * 'member' - Neither listed nor accessible except administrators, editors
                  and members.
    * 'secret' - Not listed, but available for anyone that knows the URL.
    * 'mtan' - The model is listed but only accessible once an mTAN has been
               sent to the person and entered correctly.
    * 'secret_mtan' - Not listed and only accessible once an mTAN has been
                      sent to the person and entered correctly.

    see :func:`onegov.core.security.rules.has_permission_not_logged_in`

    """

    access = meta_property(default='public')

    def extend_form(self, form_class, request: 'OrgRequest'):

        access_choices = [
            ('public', _("Public")),
            ('secret', _("Through URL only (not listed)")),
            ('private', _("Only by privileged users")),
            ('member', _("Only by privileged users and members")),
        ]

        if request.app.can_deliver_sms:
            # allowing mtan restricted models makes only sense
            # if we can deliver SMS
            access_choices.append(('mtan', _(
                "Only by privileged users or after submitting a mTAN"
            )))
            access_choices.append(('secret_mtan', _(
                "Through URL only after submitting a mTAN (not listed)"
            )))

        fields: dict[str, 'Field'] = {
            'access': RadioField(
                label=_("Access"),
                choices=access_choices,
                default='public',
                fieldset=_("Security")
            )
        }

        # FIXME: This is a bit janky, but since this field depends
        #        on this form extension field, there's unfortunately
        #        not a better place for it...
        if issubclass(form_class, ResourceForm):
            fields['occupancy_is_visible_to_members'] = BooleanField(
                label=_("Members may view occupancy"),
                description=_(
                    "The occupancy view shows the e-mail addresses "
                    "submitted with the reservations, so we only "
                    "recommend enabling this for internal resources "
                    "unless all members are sworn to uphold data privacy."
                ),
                default=None,
                depends_on=('access', '!private'),
                fieldset=_("Security")
            )

        return type('AccessForm', (form_class, ), fields)


class CoordinatesExtension(ContentExtension, CoordinatesMixin):
    """ Extends any class that has a data dictionary field with the ability
    to add coordinates to it.

    """

    def extend_form(self, form_class, request):
        return CoordinatesFormExtension(form_class).create()


class VisibleOnHomepageExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    a boolean indicating if the page should be shown on the homepage or not.

    """

    is_visible_on_homepage = meta_property()

    def extend_form(self, form_class, request):

        # do not show on root pages
        if self.parent_id is None:
            return form_class

        class VisibleOnHomepageForm(form_class):
            # pass label by keyword to give the News model access
            is_visible_on_homepage = BooleanField(
                label=_("Visible on homepage"),
                fieldset=_("Visibility"))

        return VisibleOnHomepageForm


class ContactExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    contact = content_property()

    @contact.setter  # type:ignore[no-redef]
    def contact(self, value):
        self.content['contact'] = value
        self.content['contact_html'] = to_html_ul(
            value, convert_dashes=True, with_title=True)

    @property
    def contact_html(self):
        return self.content.get('contact_html')

    def extend_form(self, form_class, request):
        class ContactPageForm(form_class):
            contact = TextAreaField(
                label=_("Address"),
                fieldset=_("Contact"),
                render_kw={'rows': 5},
                description=_("- '-' will be converted to a bulleted list\n"
                              "- Urls will be transformed into links\n"
                              "- Emails and phone numbers as well")
            )

        return ContactPageForm


class ContactHiddenOnPageExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    hide_contact = meta_property(default=False)

    def extend_form(self, form_class, request):
        class ContactHiddenOnPageForm(form_class):
            hide_contact = BooleanField(
                label=_("Hide contact info in sidebar"),
                fieldset=_("Contact"))

        return ContactHiddenOnPageForm


class NewsletterExtension(ContentExtension):
    text_in_newsletter = content_property(default=False)

    def extend_form(self, form_class, request):
        class NewsletterSettingsForm(form_class):
            text_in_newsletter = BooleanField(
                label=_('Use text instead of lead in the newsletter'),
                fieldset=_('Newsletter'),
                default=False
            )
        return NewsletterSettingsForm


class PersonLinkExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    western_name_order = content_property(default=False)

    @property
    def people(self):
        """ Returns the people linked to this content or None.

        The context specific function is temporarily stored on the
        ``context_specific_function`` attribute on each object in the
        resulting list.
        Similarly, to indicate if we want to show a particular function in the
        page of a person, ``display_function_in_person_directory`` is
        temporarily stored on each object of the resulting list.

        """

        if not self.content.get('people'):
            return None

        people = OrderedDict(self.content['people'])

        query = PersonCollection(object_session(self)).query()
        query = query.filter(Person.id.in_(people.keys()))

        result = []

        for person in query.all():
            function, show_function = people[person.id.hex]
            person.context_specific_function = function
            person.display_function_in_person_directory = show_function
            result.append(person)

        order = list(people.keys())
        result.sort(key=lambda p: order.index(p.id.hex))

        return result

    def get_selectable_people(self, request):
        """ Returns a list of people which may be linked. """

        query = PersonCollection(request.session).query()
        query = query.order_by(Person.last_name, Person.first_name)

        return query.all()

    def get_person_function_by_id(self, id):
        for _id, (function, show_func) in self.content.get('people', []):
            if id == _id:
                return function, show_func

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
            subject_function, show_subject_function = \
                self.get_person_function_by_id(subject)
            target_function, show_target_function = \
                self.get_person_function_by_id(target)

            for person, (function, show_function) in self.content['people']:

                if person == subject:
                    continue

                if person == target and direction == 'above':
                    yield subject, (subject_function, show_subject_function)
                    yield target, (target_function, show_target_function)
                    continue

                if person == target and direction == 'below':
                    yield target, (target_function, show_target_function)
                    yield subject, (subject_function, show_subject_function)
                    continue

                yield person, (function, show_function)

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
                        show_function = self._fields[field_id + '_is_visible'
                                                     + '_function'].data

                        yield person_id, (function, show_function)

            def is_ordered_people(self, existing_people):
                """ Returns True if the current list of people is ordered
                from A to Z.

                """
                if not existing_people:
                    return True

                ordered_people = OrderedDict(self.get_people_and_function(
                    selected_only=False
                ))

                existing_people = [
                    key for key, value in existing_people
                    if key in ordered_people
                ]

                sorted_existing_people = sorted(
                    existing_people, key=list(ordered_people.keys()).index)

                return existing_people == sorted_existing_people

            def populate_obj(self, obj, *args, **kwargs):
                # XXX this no longer be necessary once the person links
                # have been turned into a field, see #74
                super().populate_obj(obj, *args, **kwargs)
                self.update_model(obj)

            def process_obj(self, obj):
                # XXX this no longer be necessary once the person links
                # have been turned into a field, see #74
                super().process_obj(obj)
                self.apply_model(obj)

            def update_model(self, model):
                if 'western_ordered' in self._fields:
                    model.western_name_order = self._fields[
                        'western_ordered'].data

                previous_people = model.content.get('people', [])

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
                        key: (func, show_fun) for key, (func, show_fun)
                        in self.get_people_and_function()
                    }

                    old_people = {}
                    new_people = []

                    for id, function in previous_people:
                        if id in selected.keys():
                            existing.add(id)
                            old_people[id] = selected[id]

                    old_people = list(old_people.items())

                    for id, (func, show_fun) in self.get_people_and_function():
                        if id not in existing:
                            new_people.append((id, (func, show_fun)))

                    model.content['people'] = old_people + new_people

            def apply_model(self, model):
                if 'western_ordered' in self._fields:
                    self._fields['western_ordered'].data = (
                        model.western_name_order)

                fields = self.get_people_fields(with_function=False)
                people = dict(model.content.get('people', []))

                for field_id, field in fields:
                    if field.id.hex in people:
                        self._fields[field_id].data = True
                        function, show_function = people[field.id.hex]
                        self._fields[field_id + '_function'].data = function
                        self._fields[field_id + '_is_visible' + '_function']\
                            .data = show_function

        builder = WTFormsClassBuilder(PeoplePageForm)
        builder.set_current_fieldset(fieldset_label)

        selectable_people = self.get_selectable_people(request)
        if selectable_people:
            builder.add_field(
                field_class=BooleanField,
                field_id='western_ordered',
                label=_("Use Western ordered names"),
                description=_("For instance Franz Müller instead of Müller "
                              "Franz"),
                required=False,
                default=self.western_name_order,
            )
        for person in selectable_people:
            field_id = fieldset_id + '_' + person.id.hex
            name = f'{person.first_name} {person.last_name}' if (
                self.western_name_order) else person.title
            builder.add_field(
                field_class=BooleanField,
                field_id=field_id,
                label=name,
                required=False,
                id=person.id,
            )
            builder.add_field(
                field_class=StringField,
                field_id=field_id + '_function',
                label=request.translate(_("Function")),
                required=False,
                dependency=FieldDependency(field_id, 'y'),
                default=getattr(person, 'function', None),
                render_kw={'class_': 'indent-context-specific-function'}
            )
            builder.add_field(
                field_class=BooleanField,
                field_id=field_id + '_is_visible' + '_function',
                label=request.translate(
                    _(
                        "List this function in the page of ${name}",
                        mapping={'name': name},
                    )
                ),
                required=False,
                dependency=FieldDependency(field_id, 'y'),
                default=True if getattr(person, 'function', None) else False,
                render_kw={'class_': 'indent-context-specific-function'},
            )

        return builder.form_class


class ResourceValidationExtension(ContentExtension):

    def extend_form(self, form_class, request):

        class WithResourceValidation(form_class):

            def validate_title(self, field):
                existing = self.request.session.query(Resource).\
                    filter_by(name=normalize_for_url(field.data)).first()
                if existing and not self.model == existing:
                    raise ValidationError(
                        _("A resource with this name already exists")
                    )

        return WithResourceValidation


class PublicationExtension(ContentExtension):

    def extend_form(self, form_class, request):
        return PublicationFormExtension(form_class).create()


class HoneyPotExtension(ContentExtension):

    honeypot = meta_property(default=True)

    def extend_form(self, form_class, request):

        class HoneyPotForm(form_class):

            honeypot = BooleanField(
                label=_('Enable honey pot'),
                default=True,
                fieldset=_('Spam protection')
            )

        return HoneyPotForm


class ImageExtension(ContentExtension):

    page_image = meta_property()
    show_preview_image = meta_property(default=True)
    show_page_image = meta_property(default=True)

    def extend_form(self, form_class, request):

        class PageImageForm(form_class):
            # pass label by keyword to give the News model access
            page_image = StringField(
                label=_("Image"),
                render_kw={'class_': 'image-url'}
            )

            show_preview_image = BooleanField(
                label=_('Show image on preview on the parent page'),
                default=True,
            )

            show_page_image = BooleanField(
                label=_('Show image on page'),
                default=True,
            )

            position_choices = [
                ('in_content', _("As first element of the content")),
                ('header', _("As a full width header")),
            ]

        return PageImageForm


class GeneralFileLinkExtension(ContentExtension):
    """ Extends any class that has a files relationship to reference files from
    :class:`onegov.org.models.file.GeneralFileCollection`.

    """

    def extend_form(
        self,
        form_class: type['_FormT'],
        request: 'OrgRequest'
    ) -> type['_FormT']:

        class GeneralFileForm(form_class):  # type:ignore
            files = UploadOrSelectExistingMultipleFilesField(
                label=_("Documents"),
            )

            def populate_obj(
                self,
                obj: object,
                *args: Any,
                **kwargs: Any
            ) -> None:
                super().populate_obj(obj, *args, **kwargs)

                # transfer the publication settings to newly added files
                # TODO: maybe we should take access into account as well?
                if (
                    self.files.added_files
                    and 'publication_start' in self
                    and 'publication_end' in self
                ):
                    start = self['publication_start'].data
                    end = self['publication_end'].data
                    if start is None and end is None:
                        # nothing to do
                        return

                    now = utcnow()
                    published = True
                    if end is not None and to_timezone(end, 'UTC') < now:
                        # clear both dates and set published to False
                        published = False
                        start = None
                        end = None

                    elif start is not None:
                        if to_timezone(start, 'UTC') < now:
                            # clear the date since we're already published
                            start = None
                        else:
                            # otherwise set published to False
                            published = False

                    for file in self.files.added_files:
                        file.published = published
                        file.publish_date = start
                        file.publish_end_date = end

        return GeneralFileForm

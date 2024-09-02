import re

import json
from collections import OrderedDict
from functools import cached_property

from onegov.core.orm.abstract import MoveDirection
from onegov.core.orm.mixins import (
    content_property, dict_property, meta_property, UTCPublicationMixin)
from onegov.core.utils import normalize_for_url, to_html_ul
from onegov.form.utils import remove_empty_links
from onegov.file import File, FileCollection
from onegov.form import FieldDependency, WTFormsClassBuilder
from onegov.form.fields import ChosenSelectField
from onegov.gis import CoordinatesMixin
from onegov.org import _
from onegov.org.forms import ResourceForm
from onegov.org.forms.extensions import CoordinatesFormExtension
from onegov.org.forms.extensions import PublicationFormExtension
from onegov.org.forms.fields import UploadOrSelectExistingMultipleFilesField
from onegov.org.observer import observes
from onegov.page import Page, PageCollection
from onegov.people import Person, PersonCollection
from onegov.reservation import Resource
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session
from urlextract import URLExtract
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, ValidationError


from typing import Any, ClassVar, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from datetime import datetime
    from markupsafe import Markup
    from onegov.form.types import FormT
    from onegov.org.models import GeneralFile  # noqa: F401
    from onegov.org.request import OrgRequest
    from sqlalchemy import Column
    from sqlalchemy.orm import relationship
    from typing import type_check_only, Protocol
    from wtforms import Field

    class SupportsExtendForm(Protocol):
        def extend_form(
            self,
            form_class: type[FormT],
            request: OrgRequest
        ) -> type[FormT]: ...

    _ExtendedWithPersonLinkT = TypeVar(
        '_ExtendedWithPersonLinkT',
        bound='PersonLinkExtension'
    )


class ContentExtension:
    """ Extends classes based on :class:`onegov.core.orm.mixins.ContentMixin`
    with custom data that is stored in either 'meta' or 'content'.

    """

    if TYPE_CHECKING:
        # forward declare content attributes
        meta: Column[dict[str, Any]]
        content: Column[dict[str, Any]]

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
        form_class: type['FormT'],
        request: 'OrgRequest',
        extensions: 'Iterable[type[SupportsExtendForm]] | None' = None
    ) -> type['FormT']:
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
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:
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

    access: dict_property[str] = meta_property(default='public')

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

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

        fields: dict[str, Field] = {
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

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:
        return CoordinatesFormExtension(form_class).create()


class VisibleOnHomepageExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    a boolean indicating if the page should be shown on the homepage or not.

    """

    is_visible_on_homepage: dict_property[bool | None] = meta_property()

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        # do not show on root pages
        if self.parent_id is None:  # type:ignore[attr-defined]
            return form_class

        class VisibleOnHomepageForm(form_class):  # type:ignore
            # pass label by keyword to give the News model access
            is_visible_on_homepage = BooleanField(
                label=_("Visible on homepage"),
                fieldset=_("Visibility"))

        return VisibleOnHomepageForm


class ContactExtensionBase:
    """ Common base class for extensions that add a contact field.

    """

    contact: dict_property[str | None] = content_property()

    @contact.setter  # type:ignore[no-redef]
    def contact(self, value: str | None) -> None:
        self.content['contact'] = value  # type:ignore[attr-defined]
        # update cache
        self.__dict__['contact_html'] = to_html_ul(
            self.contact, convert_dashes=True, with_title=True
        ) if self.contact is not None else None

    @cached_property
    def contact_html(self) -> 'Markup | None':
        if self.contact is None:
            return None
        return to_html_ul(self.contact, convert_dashes=True, with_title=True)

    def get_contact_html(self, request: 'OrgRequest') -> 'Markup | None':
        return self.contact_html

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class ContactPageForm(form_class):  # type:ignore
            contact = TextAreaField(
                label=_("Address"),
                fieldset=_("Contact"),
                render_kw={'rows': 5},
                description=_("- '-' will be converted to a bulleted list\n"
                              "- Urls will be transformed into links\n"
                              "- Emails and phone numbers as well")
            )

        return ContactPageForm


class ContactExtension(ContactExtensionBase, ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """


class InheritableContactExtension(ContactExtensionBase, ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field, that can optionally be inherited from another topic.

    """

    inherit_contact: dict_property[bool] = content_property(default=False)
    contact_inherited_from: dict_property[int | None] = content_property()

    # TODO: If we end up calling this more than once per request
    #       we may want to cache this
    def get_contact_html(self, request: 'OrgRequest') -> 'Markup | None':
        if self.inherit_contact:
            if self.contact_inherited_from is None:
                return None

            pages = PageCollection(request.session)
            page = pages.by_id(self.contact_inherited_from)
            return getattr(page, 'contact_html', None)

        return self.contact_html

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        query = PageCollection(request.session).query()
        query = query.filter(Page.type == 'topic')
        query = query.filter(Page.content['contact'].isnot(None))
        if isinstance(self, Page):
            # avoid circular reference
            query = query.filter(Page.id != self.id)
        query = query.order_by(Page.title)

        class InheritableContactPageForm(form_class):  # type:ignore

            contact = TextAreaField(
                label=_("Address"),
                fieldset=_("Contact"),
                render_kw={'rows': 5},
                description=_("- '-' will be converted to a bulleted list\n"
                              "- Urls will be transformed into links\n"
                              "- Emails and phone numbers as well"),
                depends_on=('inherit_contact', '!y')
            )

            inherit_contact = BooleanField(
                label=_("Inherit address from another topic"),
                fieldset=_("Contact"),
                default=False
            )

            contact_inherited_from = ChosenSelectField(
                label=_("Topic to inherit from"),
                fieldset=_("Contact"),
                coerce=int,
                choices=query.with_entities(Page.id, Page.title).all(),
                depends_on=('inherit_contact', 'y'),
                validators=[InputRequired()]
            )

        return InheritableContactPageForm


class ContactHiddenOnPageExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    hide_contact: dict_property[bool] = meta_property(default=False)

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class ContactHiddenOnPageForm(form_class):  # type:ignore
            hide_contact = BooleanField(
                label=_("Hide contact info in sidebar"),
                fieldset=_("Contact"))

        return ContactHiddenOnPageForm


class PeopleShownOnMainPageExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field where people will be shown on bottom of main page.

    Note: Feature limited to org and town6
    """

    show_people_on_main_page: dict_property[bool] = (
        meta_property(default=False))

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class PeopleShownOnMainPageForm(form_class):  # type:ignore
            show_people_on_main_page = BooleanField(
                label=_("Show people on bottom of main page (instead of "
                        "sidebar)"),
                fieldset=_("People"))

        from onegov.org.request import OrgRequest
        # not using isinstance as e.g. FeriennetRequest inherits from
        # OrgRequest
        if type(request) is OrgRequest:
            return PeopleShownOnMainPageForm

        return form_class


class NewsletterExtension(ContentExtension):
    text_in_newsletter: dict_property[bool] = content_property(default=False)

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class NewsletterSettingsForm(form_class):  # type:ignore
            text_in_newsletter = BooleanField(
                label=_('Use text instead of lead in the newsletter'),
                fieldset=_('Newsletter'),
                default=False
            )
        return NewsletterSettingsForm


if TYPE_CHECKING:
    @type_check_only
    class PersonWithFunction(Person):
        context_specific_function: str
        display_function_in_person_directory: bool


class PersonLinkExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    western_name_order: dict_property[bool] = content_property(default=False)

    @property
    def people(self) -> list['PersonWithFunction'] | None:
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

        person: PersonWithFunction
        for person in query.all():  # type:ignore[assignment]
            function, show_function = people[person.id.hex]
            person.context_specific_function = function
            person.display_function_in_person_directory = show_function
            result.append(person)

        order = list(people.keys())
        result.sort(key=lambda p: order.index(p.id.hex))

        return result

    def get_selectable_people(self, request: 'OrgRequest') -> list[Person]:
        """ Returns a list of people which may be linked. """

        query = PersonCollection(request.session).query()
        query = query.order_by(Person.last_name, Person.first_name)

        return query.all()

    def get_person_function_by_id(self, id: str) -> tuple[str, bool]:
        for _id, (function, show_func) in self.content.get('people', []):
            if id == _id:
                return function, show_func
        raise KeyError(id)

    def move_person(
        self,
        subject: str,
        target: str,
        direction: MoveDirection
    ) -> None:
        """ Moves the subject below or above the target.

        :subject:
            The key of the person to be moved.

        :target:
            The key of the person above or below which the subject is moved.

        :direction:
            The direction relative to the target.

        """
        assert subject != target
        assert self.content.get('people')

        def new_order() -> 'Iterator[tuple[str, tuple[str, bool]]]':
            subject_function, show_subject_function = (
                self.get_person_function_by_id(subject))
            target_function, show_target_function = (
                self.get_person_function_by_id(target))

            for person, (function, show_function) in self.content['people']:

                if person == subject:
                    continue

                if person == target and direction is MoveDirection.above:
                    yield subject, (subject_function, show_subject_function)
                    yield target, (target_function, show_target_function)
                    continue

                if person == target and direction is MoveDirection.below:
                    yield target, (target_function, show_target_function)
                    yield subject, (subject_function, show_subject_function)
                    continue

                yield person, (function, show_function)

        self.content['people'] = list(new_order())

    def extend_form(
        self: '_ExtendedWithPersonLinkT',
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        # XXX this is kind of implicitly set by the builder
        fieldset_id = 'people'
        fieldset_label = _("People")

        class PeoplePageForm(form_class):  # type:ignore

            def get_people_fields(
                self,
                with_function: bool
            ) -> 'Iterator[tuple[str, Field]]':

                for field_id, field in self._fields.items():
                    if field_id.startswith(fieldset_id):
                        if with_function or not field_id.endswith('_function'):
                            yield field_id, field

            def get_people_and_function(
                self,
                selected_only: bool = True
            ) -> 'Iterator[tuple[str, tuple[str, bool]]]':

                fields = self.get_people_fields(with_function=False)

                for field_id, field in fields:
                    if not selected_only or field.data is True:
                        person_id = field.id
                        function = self._fields[field_id + '_function'].data
                        show_function = self._fields[field_id + '_is_visible'
                                                     + '_function'].data

                        yield person_id, (function, show_function)

            def is_ordered_people(
                self,
                existing_people: list[tuple[str, Any]]
            ) -> bool:
                """ Returns True if the current list of people is ordered
                from A to Z.

                """
                if not existing_people:
                    return True

                ordered_people = OrderedDict(self.get_people_and_function(
                    selected_only=False
                ))

                existing_people_keys = [
                    key for key, value in existing_people
                    if key in ordered_people
                ]

                sorted_existing_people_keys = sorted(
                    existing_people_keys,
                    key=list(ordered_people.keys()).index
                )

                return existing_people_keys == sorted_existing_people_keys

            def populate_obj(
                self,
                obj: '_ExtendedWithPersonLinkT',
                *args: Any,
                **kwargs: Any
            ) -> None:
                # XXX this no longer be necessary once the person links
                # have been turned into a field, see #74
                super().populate_obj(obj, *args, **kwargs)
                self.update_model(obj)

            def process_obj(self, obj: '_ExtendedWithPersonLinkT') -> None:
                # XXX this no longer be necessary once the person links
                # have been turned into a field, see #74
                super().process_obj(obj)
                self.apply_model(obj)

            def update_model(self, model: '_ExtendedWithPersonLinkT') -> None:
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

                    old_people_d = {}
                    new_people = []

                    for id, function in previous_people:
                        if id in selected.keys():
                            existing.add(id)
                            old_people_d[id] = selected[id]

                    old_people = list(old_people_d.items())

                    for id, (func, show_fun) in self.get_people_and_function():
                        if id not in existing:
                            new_people.append((id, (func, show_fun)))

                    model.content['people'] = old_people + new_people

            def apply_model(self, model: '_ExtendedWithPersonLinkT') -> None:
                if 'western_ordered' in self._fields:
                    self._fields['western_ordered'].data = (
                        model.western_name_order)

                fields = self.get_people_fields(with_function=False)
                people = dict(model.content.get('people', []))

                for field_id, field in fields:
                    person_id = field.id
                    if person_id in people:
                        self._fields[field_id].data = True
                        function, show_function = people[person_id]
                        self._fields[field_id + '_function'].data = function
                        self._fields[
                            field_id + '_is_visible' + '_function'
                        ].data = show_function

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
                id=person.id.hex,
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
                field_id=field_id + '_is_visible_function',
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

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class WithResourceValidation(form_class):  # type:ignore

            def validate_title(self, field: 'Field') -> None:
                existing = (
                    self.request.session.query(Resource).
                    filter_by(name=normalize_for_url(field.data)).first()
                )
                if existing and not self.model == existing:
                    raise ValidationError(
                        _("A resource with this name already exists")
                    )

        return WithResourceValidation


class PublicationExtension(ContentExtension):

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:
        return PublicationFormExtension(form_class).create()


class HoneyPotExtension(ContentExtension):

    honeypot = meta_property(default=True)

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class HoneyPotForm(form_class):  # type:ignore

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

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class PageImageForm(form_class):  # type:ignore
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


# FIXME: This is a bit of a hack because we don't have easy access to the
#        current request inside @observes methods, so we just assume any
#        urls that end with /storage/[0-9a-f]{64} are links to *our* files
FILE_URL_RE = re.compile(r'/storage/([0-9a-f]{64})$')


def _files_observer(
    self: 'GeneralFileLinkExtension',
    files: list[File],
    meta: set[str],
    publication_start: 'datetime | None' = None,
    publication_end: 'datetime | None' = None
) -> None:
    # mainly we want to observe changes to the linked files
    # but when the publication or access changes we may need
    # to change the access we propagated to the linked files
    # so we're observing those attributes too

    key = str(self.id)

    # remove ourselves if the link has been deleted
    state = inspect(self)
    for file in state.attrs.files.history.deleted:
        if key in file.meta.get('linked_accesses', ()):
            del file.linked_accesses[key]

    # we could try to determine which accesses if any need to
    # be updated using the SQLAlchemy inspect API, but it's
    # probably faster to just update all the files.
    published = getattr(self, 'published', True)
    current_access = self.access if published else 'private'
    for file in files:
        if file.meta.get('linked_accesses', {}).get(key) != current_access:
            # only trigger a DB update when necessary
            file.meta.setdefault('linked_accesses', {})[key] = current_access


def _content_file_link_observer(
    self: 'GeneralFileLinkExtension',
    content: set[str]
) -> None:
    # we don't automatically unlink files removed from the text to keep
    # things simple, otherwise we would also have to parse the text
    # prior to the change and compare the list of file ids to figure
    # out which ones have been removed, and even then it's not obvious
    # that the file was intended to be removed from the listing on the
    # side of the page, it's better to make that step explicit
    changed = self.content_fields_containing_links_to_files.intersection(
        content or ()
    )
    if not changed:
        return

    extractor = URLExtract()
    file_ids = [
        match.group(1)
        for changed_name in changed
        if (text := self.content.get(changed_name))
        for url in extractor.find_urls(text, only_unique=True)
        if (match := FILE_URL_RE.search(url))
    ]
    if not file_ids:
        return

    # HACK: On insert the id may have not been generated yet, so we need
    #       to generate it now, this assumes that the default argument
    #       provided is a single callable without a context argument
    if self.id is None:
        # for now we assume all of our default callables don't require
        # the execution context
        self.id = type(self).id.default.arg(None)

    key = str(self.id)
    session = object_session(self)
    collection = FileCollection['GeneralFile'](session, type='general')
    files = collection.query().filter(File.id.in_(file_ids))
    published = getattr(self, 'published', True)
    current_access = self.access if published else 'private'
    for file in files:
        # we may do this redundantly for some files if both observers
        # trigger, but it's easier to take the hit than to try to
        # figure out whether or not both observers triggered and in
        # which order
        if file.meta.get('linked_accesses', {}).get(key) != current_access:
            # only trigger a DB update when necessary
            file.meta.setdefault('linked_accesses', {})[key] = current_access

        # link any files that haven't already been linked
        if file not in self.files:
            self.files.append(file)


class GeneralFileLinkExtension(ContentExtension):
    """ Extends any class that has a files relationship to reference files from
    :class:`onegov.org.models.file.GeneralFileCollection`.

    Additionally any files linked within the object's content will be added to
    the explicit list of linked files and access is propagated from the owner
    of the link to the file.
    """

    content_fields_containing_links_to_files: ClassVar[set[str]] = {'text'}

    show_file_links_in_sidebar: dict_property[bool] = (
        meta_property(default=True))

    if TYPE_CHECKING:
        # forward declare required attributes
        id: Any
        files: relationship[list[File]]
        access: dict_property[str]

        def files_observer(
            self,
            files: list[File],
            meta: set[str],
            publication_start: datetime | None,
            publication_end: datetime | None
        ) -> None: ...

        def content_file_link_observer(self, content: set[str]) -> None: ...
    else:
        # in order for observes to trigger we need to use declared_attr
        @declared_attr
        def files_observer(cls):
            if issubclass(cls, UTCPublicationMixin):
                return observes(
                    'files', 'meta', 'publication_start', 'publication_end'
                )(_files_observer)

            # we can't observe the publication if it doesn't exist
            return observes('files', 'meta')(_files_observer)

        @declared_attr
        def content_file_link_observer(cls):
            return observes('content')(_content_file_link_observer)

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class GeneralFileForm(form_class):  # type:ignore
            files = UploadOrSelectExistingMultipleFilesField(
                label=_("Documents"),
                fieldset=_("Documents")
            )

            def populate_obj(self, obj: 'GeneralFileLinkExtension',
                             *args: Any, **kwargs: Any) -> None:
                super().populate_obj(obj, *args, **kwargs)

                for field_name in obj.content_fields_containing_links_to_files:
                    if field_name in self:
                        if self[field_name].data == self[
                            field_name
                        ].object_data:
                            continue

                        if (
                            (text := obj.content.get(field_name))
                            and (cleaned_text := remove_empty_links(
                                text)) != text
                        ):
                            obj.content[field_name] = cleaned_text

            show_file_links_in_sidebar = BooleanField(
                label=_("Show file links in sidebar"),
                fieldset=_("Documents"),
                description=_(
                    "Files linked in text and uploaded files are no "
                    "longer displayed in the sidebar if this option is "
                    "deselected."
                )
            )

        return GeneralFileForm


class SidebarLinksExtension(ContentExtension):

    sidepanel_links = content_property()

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class SidebarLinksForm(form_class):  # type:ignore

            sidepanel_links = StringField(
                label=_("Sidebar links"),
                fieldset=_("Sidebar links"),
                render_kw={'class_': 'many many-links'}
            )

            if TYPE_CHECKING:
                link_errors: dict[int, str]
            else:
                def __init__(self, *args, **kwargs) -> None:
                    super().__init__(*args, **kwargs)
                    self.link_errors = {}

            def on_request(self) -> None:
                if not self.sidepanel_links.data:
                    self.sidepanel_links.data = self.links_to_json(None)

            def process_obj(self, obj: 'SidebarLinksExtension') -> None:
                super().process_obj(obj)
                self.apply_model(obj)
                if not obj.sidepanel_links:
                    self.sidepanel_links.data = self.links_to_json(None)
                else:
                    self.sidepanel_links.data = self.links_to_json(
                        obj.sidepanel_links
                    )

            def populate_obj(
                self,
                obj: 'SidebarLinksExtension',
                *args: Any, **kwargs: Any
            ) -> None:
                super().populate_obj(obj, *args, **kwargs)
                obj.sidepanel_links = self.json_to_links(
                    self.sidepanel_links.data) or None

            def validate_sidepanel_links(self, field: StringField) -> None:
                for text, url in self.json_to_links(self.sidepanel_links.data):
                    if text and not url:
                        raise ValidationError(
                            _('Please add an url to each link'))
                    if url and not re.match(r'^(http://|https://|/)', url):
                        raise ValidationError(
                            _('Your URLs must start with http://,'
                              ' https:// or /'
                              ' (for internal links)')
                        )

            def json_to_links(
                self,
                text: str | None = None
            ) -> list[tuple[str | None, str | None]]:
                result = []

                for value in json.loads(text or '{}').get('values', []):
                    if value['link'] or value['text']:
                        result.append((value['text'], value['link']))

                return result

            def links_to_json(
                self,
                links: 'Sequence[tuple[str | None, str | None]] | None'
            ) -> str:
                sidepanel_links = links or []

                return json.dumps({
                    'labels': {
                        'text': self.request.translate(_("Text")),
                        'link': self.request.translate(_("URL")),
                        'add': self.request.translate(_("Add")),
                        'remove': self.request.translate(_("Remove")),
                    },
                    'values': [
                        {
                            'text': l[0],
                            'link': l[1],
                            'error': self.link_errors.get(ix, '')
                        } for ix, l in enumerate(sidepanel_links)
                    ]
                })

        return SidebarLinksForm


class DeletableContentExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    mark the content as deletable after reaching the end date. A cronjob will
    periodically check for 'deletable' content with expired end date and
    delete it e.g. Directories.

    """

    delete_when_expired: dict_property[bool] = content_property(default=False)

    def extend_form(
        self,
        form_class: type['FormT'],
        request: 'OrgRequest'
    ) -> type['FormT']:

        class DeletableContentForm(form_class):  # type:ignore
            delete_when_expired = BooleanField(
                label=_("Delete content when expired"),
                description=_("This content is automatically deleted if the "
                              "end date is in the past"),
                fieldset=_("Delete content")
            )

        return DeletableContentForm

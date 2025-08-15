from __future__ import annotations

import re

import json
from collections import OrderedDict
from functools import cached_property

from markupsafe import Markup

from onegov.core.i18n import get_translation_bound_meta
from onegov.core.orm.abstract import MoveDirection
from onegov.core.orm.mixins import (
    content_property, dict_property, meta_property, UTCPublicationMixin)
from onegov.core.templates import render_macro
from onegov.core.utils import normalize_for_url, to_html_ul
from onegov.form.utils import remove_empty_links
from onegov.file import File, FileCollection
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.gis import CoordinatesMixin
from onegov.org import _
from onegov.org.forms import ResourceForm
from onegov.org.forms.extensions import (
    CoordinatesFormExtension, PushNotificationFormExtension)
from onegov.org.forms.extensions import PublicationFormExtension
from onegov.org.forms.fields import UploadOrSelectExistingMultipleFilesField
from onegov.org.observer import observes
from onegov.page import Page, PageCollection
from onegov.people import Person, PersonCollection
from onegov.reservation import Resource
from sqlalchemy import desc, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import object_session
from urlextract import URLExtract
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import FieldList
from wtforms.fields import FormField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.utils import unset_value
from wtforms.validators import InputRequired, ValidationError


from typing import Any, ClassVar, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from datetime import datetime
    from onegov.form.types import FormT
    from onegov.org.models import GeneralFile  # noqa: F401
    from onegov.org.request import OrgRequest
    from onegov.org.models import ImageSet
    from sqlalchemy import Column
    from sqlalchemy.orm import relationship
    from typing import type_check_only, Protocol
    from wtforms import Field
    from wtforms.fields.choices import _Choice
    from wtforms.fields.core import _Filter
    from wtforms.meta import _MultiDictLikeWithGetlist

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


def json_to_links(
    text: str | None = None
) -> list[tuple[str | None, str | None]]:

    if not text:
        return []

    return [
        (value['text'], link)
        for value in json.loads(text).get('values', [])
        if (link := value['link']) or value['text']
    ]


class ContentExtension:
    """ Extends classes based on :class:`onegov.core.orm.mixins.ContentMixin`
    with custom data that is stored in either 'meta' or 'content'.

    """

    if TYPE_CHECKING:
        # forward declare content attributes
        meta: Column[dict[str, Any]]
        content: Column[dict[str, Any]]

    @property
    def content_extensions(self) -> Iterator[type[ContentExtension]]:
        """ Returns all base classes of the current class which themselves have
        ``ContentExtension`` as baseclass.

        """
        for cls in self.__class__.__bases__:
            if ContentExtension in cls.__bases__:
                yield cls

    def with_content_extensions(
        self,
        form_class: type[FormT],
        request: OrgRequest,
        extensions: Iterable[type[SupportsExtendForm]] | None = None
    ) -> type[FormT]:
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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:
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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        access_choices = [
            ('public', _('Public')),
            ('secret', _('Through URL only (not listed)')),
            ('private', _('Only by privileged users')),
            ('member', _('Only by privileged users and members')),
        ]

        if request.app.can_deliver_sms:
            # allowing mtan restricted models makes only sense
            # if we can deliver SMS
            access_choices.append(('mtan', _(
                'Only by privileged users or after submitting a mTAN'
            )))
            access_choices.append(('secret_mtan', _(
                'Through URL only after submitting a mTAN (not listed)'
            )))

        fields: dict[str, Field] = {
            'access': RadioField(
                label=_('Access'),
                choices=access_choices,
                default='public',
                fieldset=_('Security')
            )
        }

        # FIXME: This is a bit janky, but since this field depends
        #        on this form extension field, there's unfortunately
        #        not a better place for it...
        if issubclass(form_class, ResourceForm):
            fields['occupancy_is_visible_to_members'] = BooleanField(
                label=_('Members may view occupancy'),
                description=_(
                    'The occupancy view shows the e-mail addresses '
                    'submitted with the reservations, so we only '
                    'recommend enabling this for internal resources '
                    'unless all members are sworn to uphold data privacy.'
                ),
                default=None,
                depends_on=('access', '!private'),
                fieldset=_('Security')
            )

        return type('AccessForm', (form_class, ), fields)


class CoordinatesExtension(ContentExtension, CoordinatesMixin):
    """ Extends any class that has a data dictionary field with the ability
    to add coordinates to it.

    """

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:
        return CoordinatesFormExtension(form_class).create()


class VisibleOnHomepageExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    a boolean indicating if the page should be shown on the homepage or not.

    """

    is_visible_on_homepage: dict_property[bool | None] = meta_property()

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        # do not show on root pages
        if self.parent_id is None:  # type:ignore[attr-defined]
            return form_class

        class VisibleOnHomepageForm(form_class):  # type:ignore
            # pass label by keyword to give the News model access
            is_visible_on_homepage = BooleanField(
                label=_('Visible on homepage'),
                fieldset=_('Visibility'))

        return VisibleOnHomepageForm


class ContactExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field, that can optionally be inherited from another topic.

    """

    contact: dict_property[str | None] = content_property()

    @contact.setter  # type:ignore[no-redef]
    def contact(self, value: str | None) -> None:
        self.content['contact'] = value
        if self.inherit_contact:
            # no need to update the cache
            return

        # update cache
        self.__dict__['contact_html'] = to_html_ul(
            value, convert_dashes=True, with_title=True
        ) if value is not None else None

    inherit_contact: dict_property[bool] = content_property(default=False)

    @inherit_contact.setter  # type:ignore[no-redef]
    def inherit_contact(self, value: bool) -> None:
        self.content['inherit_contact'] = value

        # clear cache (don't update eagerly since it involves a query)
        if 'contact_html' in self.__dict__:
            del self.__dict__['contact_html']

    contact_inherited_from: dict_property[int | None] = content_property()

    @contact_inherited_from.setter  # type:ignore[no-redef]
    def contact_inherited_from(self, value: int | None) -> None:
        self.content['contact_inherited_from'] = value
        if not self.inherit_contact:
            # no need to clear the cache
            return

        # clear cache (don't update eagerly since it involves a query)
        if 'contact_html' in self.__dict__:
            del self.__dict__['contact_html']

    @cached_property
    def contact_html(self) -> Markup | None:
        if self.inherit_contact:
            if self.contact_inherited_from is None:
                return None

            pages = PageCollection(object_session(self))
            page = pages.by_id(self.contact_inherited_from)
            contact = getattr(page, 'contact', None)
        else:
            contact = self.contact

        if contact is None:
            return None
        return to_html_ul(contact, convert_dashes=True, with_title=True)

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        query = PageCollection(request.session).query()
        query = query.filter(Page.type == 'topic')
        query = query.filter(Page.content['contact'].isnot(None))
        if isinstance(self, Page):
            # avoid circular reference
            query = query.filter(Page.id != self.id)
        query = query.order_by(Page.title)

        # Ancestor pages should appear first in the list
        pinned = {
            page.id: page.title
            for page in self.ancestors
            if page.content.get('contact')
        } if isinstance(self, Page) else {}

        choices: list[_Choice] = [
            (page_id, title)
            for page_id, title in query.with_entities(Page.id, Page.title)
            if page_id not in pinned
        ]

        if pinned:
            choices.insert(0, (-1, '-'*32, {'disabled': 'disabled'}))
            for choice in reversed(pinned.items()):
                choices.insert(0, choice)

        class ContactPageForm(form_class):  # type:ignore
            contact = TextAreaField(
                label=_('Address'),
                fieldset=_('Contact'),
                render_kw={'rows': 5},
                description=_("- '-' will be converted to a bulleted list\n"
                              "- Urls will be transformed into links\n"
                              "- Emails and phone numbers as well")
            )

            inherit_contact = BooleanField(
                label=_('Inherit address from another topic'),
                fieldset=_('Contact'),
                default=False
            )

            contact_inherited_from = ChosenSelectField(
                label=_('Topic to inherit from'),
                fieldset=_('Contact'),
                coerce=int,
                choices=choices,
                depends_on=('inherit_contact', 'y'),
                validators=[InputRequired()]
            )

        return ContactPageForm


class ContactHiddenOnPageExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with a simple
    contacts field.

    """

    hide_contact: dict_property[bool] = meta_property(default=False)

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class ContactHiddenOnPageForm(form_class):  # type:ignore
            hide_contact = BooleanField(
                label=_('Hide contact info in sidebar'),
                fieldset=_('Contact'))

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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class PeopleShownOnMainPageForm(form_class):  # type:ignore
            show_people_on_main_page = BooleanField(
                label=_('Show people on bottom of main page (instead of '
                        'sidebar)'),
                fieldset=_('People'))

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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

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
        person: str
        context_specific_function: str
        display_function_in_person_directory: bool


class PersonLinkExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    western_name_order: dict_property[bool] = content_property(default=False)

    @property
    def people(self) -> list[PersonWithFunction] | None:
        """ Returns the people linked to this content or None.

        The context specific function is temporarily stored on the
        ``context_specific_function`` attribute on each object in the
        resulting list.
        Similarly, to indicate if we want to show a particular function in the
        page of a person, ``display_function_in_person_directory`` is
        temporarily stored on each object of the resulting list.

        """

        if not (people_items := self.content.get('people')):
            return None

        people = OrderedDict(people_items)
        query = PersonCollection(object_session(self)).query()
        query = query.filter(Person.id.in_(people.keys()))

        result = []

        person: PersonWithFunction
        for person in query.all():  # type:ignore[assignment]
            function, show_function = people[person.id.hex]
            person.person = person.id.hex
            person.context_specific_function = function
            person.display_function_in_person_directory = show_function
            result.append(person)

        order = list(people.keys())
        result.sort(key=lambda p: order.index(p.id.hex))

        return result

    def get_selectable_people(self, request: OrgRequest) -> list[Person]:
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

        def new_order() -> Iterator[tuple[str, tuple[str, bool]]]:
            subject_function, show_subject_function = (
                self.get_person_function_by_id(subject))

            for person, (function, show_function) in self.content['people']:

                if person == subject:
                    continue

                if person == target and direction is MoveDirection.above:
                    yield subject, (subject_function, show_subject_function)

                yield person, (function, show_function)

                if person == target and direction is MoveDirection.below:
                    yield subject, (subject_function, show_subject_function)

        self.content['people'] = list(new_order())

    def extend_form(
        self: _ExtendedWithPersonLinkT,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        selectable_people = self.get_selectable_people(request)
        if not selectable_people:
            # no need to extend the form
            return form_class

        selected = dict((self.content or {}).get('people', []))

        def choice(person: Person) -> _Choice:
            if self.western_name_order:
                name = f'{person.first_name} {person.last_name}'
            else:
                name = person.title

            render_kw = {}

            # prioritize existing function
            if chosen := selected.get(person.id.hex):
                render_kw['data-function'], show = chosen
                render_kw['data-show'] = 'true' if show else 'false'
            elif function := getattr(person, 'function', None):
                render_kw['data-function'] = function

            return person.id.hex, name, render_kw

        choices: list[_Choice] = [
            choice(person) for person in selectable_people
        ]
        choices.insert(0, ('', ''))

        class PersonForm(Form):
            person = SelectField(
                label='',
                choices=choices,
                render_kw={
                    'class_': 'people-select',
                    'data-placeholder': request.translate(
                        _('Select additional person')
                    ),
                    'data-no_results_text': request.translate(
                        _('No results match')
                    ),
                }
            )
            context_specific_function = TextAreaField(
                label=_('Function'),
                depends_on=('person', '!'),
                render_kw={'class_': 'indent-form-field'},
            )
            display_function_in_person_directory = BooleanField(
                label=_('List this function in the page of this person'),
                depends_on=('person', '!'),
                render_kw={'class_': 'indent-form-field'},
            )

        # HACK: Get translations working in FormField
        #       We should probably make our own FormField, that doesn't
        #       need this workaround
        meta = get_translation_bound_meta(
            PersonForm.Meta,
            request.get_translate(for_chameleon=False)
        )
        meta.locales = [request.locale, 'en'] if request.locale else []
        PersonForm.Meta = meta

        if TYPE_CHECKING:
            FieldBase = FieldList[FormField[PersonForm]]  # noqa: N806
        else:
            FieldBase = FieldList  # noqa: N806

        class PeopleField(FieldBase):
            def is_ordered_people(self, people: list[tuple[str, Any]]) -> bool:
                people_dict = dict(people)
                return [
                    person.id.hex
                    for person in selectable_people
                    if person.id.hex in people_dict
                ] == list(people_dict.keys())

            def process(
                self,
                formdata: _MultiDictLikeWithGetlist | None,
                data: Any = unset_value,
                extra_filters: Sequence[_Filter] | None = None
            ) -> None:

                # FIXME: I'm not quite sure why we need to do this
                #        but it looks like the last_index gets updated
                #        to 0 by something, so we start counting at 1
                #        instead of 0, which breaks the field
                self.last_index = -1
                super().process(formdata, data, extra_filters)

                # always have an empty extra entry
                if formdata is None and self[-1].form.person.data is not None:
                    self.append_entry()

            def populate_obj(self, obj: object, name: str) -> None:
                assert name == 'people'
                assert hasattr(obj, 'content')

                previous_people = obj.content.get('people', [])
                people_values = {
                    person_id: (
                        item['context_specific_function'],
                        item['display_function_in_person_directory']
                    )
                    for item in self.data
                    # skip de-selected entries
                    if (person_id := item['person'])
                }

                if self.is_ordered_people(previous_people):
                    # if the people are ordered a-z, we take the ordering from
                    # selectable_people, which is already ordered
                    obj.content['people'] = [
                        (person.id.hex, v)
                        for person in selectable_people
                        if (v := people_values.get(person.id.hex)) is not None
                    ]
                else:
                    # otherwise we just use the given order
                    obj.content['people'] = list(people_values.items())

        field_macro = request.template_loader.macros['field']
        # FIXME: It is not ideal that we have to pass a dummy form along to
        #        the field render macro, we should try to move the description
        #        rendering either into the form meta, so it can be accessed
        #        from the field or move it to the request, since it doesn't
        #        actually depend on the specific form
        dummy_form = request.get_form(Form, csrf_support=False)

        def people_widget(field: FieldBase, **kwargs: Any) -> Markup:
            request.include('people-select')
            return Markup('<br>').join(
                Markup('<div id="{}">{}</div>').format(f.id, f())
                for f in field
            )

        class PeoplePageForm(form_class):  # type:ignore

            western_name_order = BooleanField(
                label=_('Use Western ordered names'),
                description=_('For instance Franz Müller instead of Müller '
                              'Franz'),
                fieldset=_('People'),
            )

            people = PeopleField(
                FormField(
                    PersonForm,
                    widget=lambda field, **kw: Markup('').join(
                        Markup('<div><label>{}</label></div>').format(render_macro(
                            field_macro,
                            request,
                            {
                                'field': f,
                                # FIXME: only used for rendering descriptions
                                #        we should probably move this logic
                                #        into a template macro or a method on
                                #        CoreRequest, this doesn't really need
                                #        to be part of Form, we could also move
                                #        it to the form meta and access it
                                #        through the field instead
                                'form': dummy_form
                            }
                        )) for f in field
                    )
                ),
                label=_('People'),
                fieldset=_('People'),
                # we always have at least one empty entry
                min_entries=1,
                widget=people_widget,
            )

        return PeoplePageForm


class ResourceValidationExtension(ContentExtension):

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class WithResourceValidation(form_class):  # type:ignore

            def validate_title(self, field: Field) -> None:
                existing = (
                    self.request.session.query(Resource).
                    filter_by(name=normalize_for_url(field.data)).first()
                )
                if existing and not self.model == existing:
                    raise ValidationError(
                        _('A resource with this name already exists')
                    )

        return WithResourceValidation


class PublicationExtension(ContentExtension):

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:
        return PublicationFormExtension(form_class).create()


class PushNotificationExtension(ContentExtension):

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:
        return PushNotificationFormExtension(form_class).create()


class HoneyPotExtension(ContentExtension):

    honeypot = meta_property(default=True)

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class PageImageForm(form_class):  # type:ignore
            # pass label by keyword to give the News model access
            page_image = StringField(
                label=_('Image'),
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
                ('in_content', _('As first element of the content')),
                ('header', _('As a full width header')),
            ]

        return PageImageForm


# FIXME: This is a bit of a hack because we don't have easy access to the
#        current request inside @observes methods, so we just assume any
#        urls that end with /storage/[0-9a-f]{64} are links to *our* files
FILE_URL_RE = re.compile(r'/storage/([0-9a-f]{64})$')


def _files_observer(
    self: GeneralFileLinkExtension,
    files: list[File],
    meta: set[str],
    publication_start: datetime | None = None,
    publication_end: datetime | None = None
) -> None:
    # mainly we want to observe changes to the linked files
    # but when the publication or access changes we may need
    # to change the access we propagated to the linked files
    # so we're observing those attributes too

    key = str(self.id)

    # remove ourselves if the link has been deleted
    state = inspect(self)
    for file in state.attrs.files.history.deleted:
        if (key in file.meta.get('linked_accesses', ()) and
                hasattr(file, 'linked_accesses')):
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
    self: GeneralFileLinkExtension,
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
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class GeneralFileForm(form_class):  # type:ignore
            files = UploadOrSelectExistingMultipleFilesField(
                label=_('Documents'),
                fieldset=_('Documents')
            )

            def populate_obj(self, obj: GeneralFileLinkExtension,
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
                label=_('Show file links in sidebar'),
                fieldset=_('Documents'),
                description=_(
                    'Files linked in text and uploaded files are no '
                    'longer displayed in the sidebar if this option is '
                    'deselected.'
                )
            )

        return GeneralFileForm


class SidebarLinksExtension(ContentExtension):

    sidepanel_links = content_property()

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class SidebarLinksForm(form_class):  # type:ignore

            sidepanel_links = StringField(
                label=_('Sidebar links'),
                fieldset=_('Sidebar links'),
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

            def process_obj(self, obj: SidebarLinksExtension) -> None:
                super().process_obj(obj)
                if not hasattr(obj, 'sidepanel_links'):
                    self.sidepanel_links.data = self.links_to_json(None)
                else:
                    self.sidepanel_links.data = self.links_to_json(
                        obj.sidepanel_links
                    )

            def populate_obj(
                self,
                obj: SidebarLinksExtension,
                *args: Any, **kwargs: Any
            ) -> None:
                super().populate_obj(obj, *args, **kwargs)
                if hasattr(obj, 'sidepanel_links'):
                    obj.sidepanel_links = json_to_links(
                        self.sidepanel_links.data) or None

            def validate_sidepanel_links(self, field: StringField) -> None:
                for text, url in json_to_links(self.sidepanel_links.data):
                    if text and not url:
                        raise ValidationError(
                            _('Please add an url to each link'))
                    if url and not re.match(r'^(http://|https://|/)', url):
                        raise ValidationError(
                            _('Your URLs must start with http://,'
                              ' https:// or /'
                              ' (for internal links)')
                        )

            def links_to_json(
                self,
                links: Sequence[tuple[str | None, str | None]] | None
            ) -> str:
                sidepanel_links = links or []

                return json.dumps({
                    'labels': {
                        'text': self.request.translate(_('Text')),
                        'link': self.request.translate(_('URL')),
                        'add': self.request.translate(_('Add')),
                        'remove': self.request.translate(_('Remove')),
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


class SidebarContactLinkExtension(ContentExtension):
    """ Like SidebarLinkExtension but the links are shown below the contact
    field. We knowingly duplicate some code here .
    """

    sidepanel_contact = content_property()

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class SidebarContactLinkForm(form_class):  # type:ignore

            sidepanel_contact = StringField(
                label=_('Contact link'),
                fieldset=_('Sidebar contact'),
                render_kw={'class_': 'many many-links'}
            )

            if TYPE_CHECKING:
                contact_errors: dict[int, str]
            else:
                def __init__(self, *args, **kwargs) -> None:
                    super().__init__(*args, **kwargs)
                    self.contact_errors = {}

            def on_request(self) -> None:
                if not self.sidepanel_contact.data:
                    self.sidepanel_contact.data = self.contact_links_to_json(
                        None)

            def process_obj(self, obj: SidebarContactLinkExtension) -> None:
                super().process_obj(obj)
                if not hasattr(obj, 'sidepanel_contact'):
                    self.sidepanel_contact.data = self.contact_links_to_json(
                        None)
                else:
                    self.sidepanel_contact.data = self.contact_links_to_json(
                        obj.sidepanel_contact
                    )

            def populate_obj(
                self,
                obj: SidebarContactLinkExtension,
                *args: Any, **kwargs: Any
            ) -> None:
                super().populate_obj(obj, *args, **kwargs)
                if hasattr(obj, 'sidepanel_contact'):
                    obj.sidepanel_contact = json_to_links(
                        self.sidepanel_contact.data) or None

            def validate_sidepanel_contact(self, field: StringField) -> None:
                for text, link in json_to_links(
                        self.sidepanel_contact.data
                ):
                    if text and not link:
                        raise ValidationError(
                            _('Please provide a URL if contact link text is '
                              'set'))
                    if link and not text:
                        raise ValidationError(
                            _('Please provide link text if contact URL is '
                              'set'))
                    if link and not re.match(r'^(http://|https://|/)',
                                             link):
                        raise ValidationError(
                            _('Your URLs must start with http://,'
                              ' https:// or /'
                              ' (for internal links)')
                        )

            def contact_links_to_json(
                self,
                links: Sequence[tuple[str | None, str | None]] | None
            ) -> str:
                contact_links = links or []

                return json.dumps({
                    'labels': {
                        'text': self.request.translate(_('Contact Text')),
                        'link': self.request.translate(_('Contact URL')),
                        'add': self.request.translate(_('Add')),
                        'remove': self.request.translate(_('Remove')),
                    },
                    'values': [
                        {
                            'text': l[0],
                            'link': l[1],
                            'error': self.contact_errors.get(ix, '')
                        } for ix, l in enumerate(contact_links)
                    ]
                })

        return SidebarContactLinkForm


class DeletableContentExtension(ContentExtension):
    """ Extends any class that has a meta dictionary field with the ability to
    mark the content as deletable after reaching the end date. A cronjob will
    periodically check for 'deletable' content with expired end date and
    delete it e.g. Directories.

    """

    delete_when_expired: dict_property[bool] = content_property(default=False)

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        class DeletableContentForm(form_class):  # type:ignore
            delete_when_expired = BooleanField(
                label=_('Delete content when expired'),
                description=_('This content is automatically deleted if the '
                              'end date is in the past'),
                fieldset=_('Delete content')
            )

        return DeletableContentForm


class InlinePhotoAlbumExtension(ContentExtension):
    """ Adds ability to reference photo albums (ImageSets) and show them
    inline at the end of the content of the page.

    """

    photo_album_id: dict_property[str | None] = content_property(default=None)

    @property
    def photo_album(self) -> ImageSet | None:
        from onegov.org.models import ImageSetCollection
        if not self.photo_album_id:
            return None
        return ImageSetCollection(object_session(self)).by_id(
            self.photo_album_id
        )

    def extend_form(
        self,
        form_class: type[FormT],
        request: OrgRequest
    ) -> type[FormT]:

        from onegov.org.models import ImageSetCollection
        from onegov.org.models import ImageSet
        albums: list[ImageSet] = (  # noqa: TC201
            ImageSetCollection(request.session).query().order_by(
                desc(ImageSet.last_change), ImageSet.title).all())
        if not albums:
            return form_class

        class PhotoAlbumForm(form_class):  # type:ignore

            choices = [('', '')] + [
                (album.id, album.title) for album in albums
            ]
            photo_album_id = SelectField(
                label=_('Photo album'),
                fieldset=_('Photo album'),
                choices=choices,
                name='photo_album_id',
            )

            def process_obj(self, obj: InlinePhotoAlbumExtension) -> None:
                super().process_obj(obj)
                if obj.photo_album_id:
                    self.photo_album_id.data = obj.photo_album_id

            def populate_obj(
                self,
                obj: InlinePhotoAlbumExtension,
                *args: Any,
                **kwargs: Any
            ) -> None:
                super().populate_obj(obj, *args, **kwargs)
                obj.photo_album_id = self.photo_album_id.data or None

        return PhotoAlbumForm

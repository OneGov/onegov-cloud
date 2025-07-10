from __future__ import annotations
from sqlalchemy.orm import object_session
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.utils import unset_value

from markupsafe import Markup
from onegov.core.orm.mixins import content_property, dict_property
from onegov.core.templates import render_macro
from onegov.form import Form
from onegov.form.types import FormT
from onegov.org.models import ContentExtension
from onegov.org.request import OrgRequest

from typing import TYPE_CHECKING, TypeVar, Any
from collections.abc import Sequence

from wtforms.fields import TextAreaField
from wtforms.fields import BooleanField

from onegov.org import _
from onegov.org.models import RISParliamentarian

if TYPE_CHECKING:
    from wtforms.fields.choices import _Choice
    from wtforms.fields import SelectField
    from wtforms.fields.core import _Filter
    from wtforms.meta import _MultiDictLikeWithGetlist

    _ExtendedWithParticipationT = TypeVar(
        '_ExtendedWithParticipationT',
        bound='PoliticalBusinessParticipationExtension'
    )


class PoliticalBusinessParticipationExtension(ContentExtension):
    """ Extends any class that has a content dictionary field with the ability
    to reference people from :class:`onegov.people.PersonCollection`.

    """

    western_name_order: dict_property[bool] = content_property(default=False)

    @property
    def people(self) -> list[RISParliamentarian] | None:
        query = RISParliamentarian(object_session(self)).query()
        query = query.filter(RISParliamentarian.active == True)

        # result = []
        #
        # person: RISParliamentarian
        # for person in query.all():  # type:ignore[assignment]
        #     function, show_function = people[person.id.hex]
        #     person.person = person.id.hex
        #     person.context_specific_function = function
        #     person.display_function_in_person_directory = show_function
        #     result.append(person)
        #
        # order = list(people.keys())
        # result.sort(key=lambda p: order.index(p.id.hex))
        #
        # return result
        return query.all()

    def get_selectable_people(self, request: OrgRequest) -> list[RISParliamentarian]:
        """ Returns a list of people which may be linked. """

        query = RISParliamentarian(request.session).query()
        query = query.order_by(RISParliamentarian.last_name, RISParliamentarian.first_name)

        return query.all()

    def get_person_function_by_id(self, id: str) -> tuple[str, bool]:
        for _id, (function, show_func) in self.content.get('people', []):
            if id == _id:
                return function, show_func
        raise KeyError(id)

    def extend_form(
            # self: _ExtendedWithParticipationT,
            self,
            form_class: type[FormT],
            request: OrgRequest
    ) -> type[FormT]:

        selectable_people = self.get_selectable_people(request)
        if not selectable_people:
            # no need to extend the form
            return form_class

        selected = dict((self.content or {}).get('people', []))

        # def choice(person: RISParliamentarian) -> _Choice:
        #     render_kw = {}
        #
        #     # prioritize existing function
        #     if chosen := selected.get(person.id.hex):
        #         render_kw['data-function'], show = chosen
        #         render_kw['data-show'] = 'true' if show else 'false'
        #     elif function := getattr(person, 'function', None):
        #         render_kw['data-function'] = function
        #
        #     return person.id.hex, person.display_name, render_kw

        choices: list[_Choice] = selectable_people
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
        # meta = get_translation_bound_meta(
        #     PersonForm.Meta,
        #     request.get_translate(for_chameleon=False)
        # )
        # meta.locales = [request.locale, 'en'] if request.locale else []
        # PersonForm.Meta = meta

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

        # FIXME: verify if still needed
        class PeoplePageForm(form_class):  # type:ignore

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

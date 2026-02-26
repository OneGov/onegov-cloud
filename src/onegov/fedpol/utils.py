from __future__ import annotations

from onegov.form import Form
from onegov.form.parser import parse_form
from onegov.form.utils import get_fields_from_class
from onegov.form.validators import If


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import FormDefinition, FormSubmission


# NOTE: This is pretty fragile and depends on us working with a form
#       parsed from formcode, rather than with a form we defined
def get_step_form(
    owner: FormDefinition | FormSubmission,
    step: int
) -> type[Form] | None:

    if step < 1:
        return None

    # FIXME: How do we handle form extensions better? For a honeypot
    #        we would want to extend each step, but for other extensions
    #        we may only want to extend the final step or add a step
    #        for the extension...
    form_class = parse_form(owner.definition)

    class StepForm(Form):
        _source = getattr(form_class, '_source', None)
        is_step = True
        step_name: str | None = None

    current_step = 0
    current_fieldset: str | bool | None = False
    all_fields = get_fields_from_class(form_class)
    for key, unbound_field in all_fields:
        fieldset = unbound_field.kwargs.get('fieldset')
        if fieldset != current_fieldset:
            current_fieldset = fieldset
            current_step += 1

        if current_step > step:
            break

        if current_step == step:
            assert not isinstance(current_fieldset, bool)
            StepForm.step_name = current_fieldset
            cloned_field = unbound_field.field_class(
                *unbound_field.args,
                **unbound_field.kwargs
            )
            setattr(StepForm, key, cloned_field)

    # NOTE: This means we only have one step.
    #       So we return the original form.
    if current_step == 1:
        return owner.extend_form_class(form_class, owner.extensions or [])

    # NOTE: This means the step doesn't exist
    if current_step < step:
        return None

    filtered = dict(get_fields_from_class(StepForm))
    if not filtered:
        return None

    dropped_keys = {key for key, _ in all_fields} - filtered.keys()
    for key, unbound_field in filtered.items():
        kwargs = unbound_field.kwargs
        kwargs.pop('fieldset', None)
        render_kw = kwargs.get('render_kw')
        if not render_kw:
            continue

        if 'data-depends-on' not in render_kw:
            continue

        # NOTE: Maybe remove dependency on previous step
        dependency = render_kw['data-depends-on']
        assert ';' not in dependency
        depends_on = dependency.split('/', 1)[0]
        if depends_on not in dropped_keys:
            continue

        del render_kw['data-depends-on']

        validators = kwargs.get('validators')
        if not validators:
            continue

        if not isinstance(validators[0], If):
            continue

        validators = [
            *validators[0].validators,
            *validators[2:]
        ]

    return owner.extend_form_class(StepForm, owner.extensions or [])

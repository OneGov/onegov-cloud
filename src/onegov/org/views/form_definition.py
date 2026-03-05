from __future__ import annotations

import morepath
import requests

from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection, FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.gis import Coordinates
from onegov.org import _, OrgApp, log
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import FormDefinitionForm
from onegov.org.forms.form_definition import FormDefinitionUrlForm
from onegov.org.layout import FormEditorLayout, FormSubmissionLayout
from onegov.org.models import BuiltinFormDefinition, CustomFormDefinition
from onegov.org.models.form import submission_deletable
from webob import exc
from webob import Response

from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.core.layout import Layout
    from onegov.core.types import RenderData
    from onegov.form import Form, FormSubmission
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Session
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


def get_form_class(
    model: BuiltinFormDefinition | CustomFormDefinition | FormCollection,
    request: OrgRequest
) -> type[FormDefinitionForm]:

    if isinstance(model, FormCollection):
        model = CustomFormDefinition()

    form_classes = {
        'builtin': FormDefinitionForm,
        'custom': FormDefinitionForm
    }

    return model.with_content_extensions(form_classes[model.type], request)


# FIXME: format_date should really be a utility function on the request
#        first and on the layout second, passing around layouts in contexts
#        where we don't actually always have one is weird
def get_hints(
    layout: Layout,
    window: FormRegistrationWindow | None
) -> Iterator[tuple[str, str]]:

    if not window:
        return

    if window.in_the_past:
        yield 'stop', _('The registration has ended')
    elif not window.enabled:
        yield 'stop', _('The registration is closed')

    if window.enabled and window.in_the_future:
        yield 'date', _('The registration opens on ${day}, ${date}', mapping={
            'day': layout.format_date(window.start, 'weekday_long'),
            'date': layout.format_date(window.start, 'date_long')
        })

    if window.enabled and window.in_the_present:
        yield 'date', _('The registration closes on ${day}, ${date}', mapping={
            'day': layout.format_date(window.end, 'weekday_long'),
            'date': layout.format_date(window.end, 'date_long')
        })

        if window.limit and window.overflow:
            yield 'count', _("There's a limit of ${count} attendees", mapping={
                             'count': window.limit
                             })

        if window.limit and not window.overflow:
            spots = window.available_spots

            if spots == 0:
                yield 'stop', _('There are no spots left')
            elif spots == 1:
                yield 'count', _('There is one spot left')
            else:
                yield 'count', _('There are ${count} spots left', mapping={
                    'count': spots
                })


def handle_form_change_name(
    form: FormDefinitionT,
    session: Session,
    new_name: str
) -> FormDefinitionT:

    new_form = form.for_new_name(new_name)
    session.add(new_form)
    session.flush()

    submissions = form.submissions
    windows = form.registration_windows

    with session.no_autoflush:
        # This placed elsewhere will not work
        form.submissions = []
        form.registration_windows = []

        # assigning the whole list directly will not work
        for s in submissions:
            s.name = new_name
            new_form.submissions.append(s)
        for w in windows:
            w.name = new_name
            new_form.registration_windows.append(w)

    session.flush()

    assert not form.submissions
    assert not form.registration_windows
    return new_form


@OrgApp.form(
    model=FormDefinition, form=FormDefinitionUrlForm,
    template='form.pt', permission=Private,
    name='change-url'
)
def handle_change_form_name(
    self: FormDefinition,
    request: OrgRequest,
    form: FormDefinitionUrlForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:
    """Since the name used for the url is the primary key, we create a new
    FormDefinition to make our live easier """
    site_title = _('Change URL')
    if form.submitted(request):
        assert form.name.data is not None
        new_form = handle_form_change_name(
            self, request.session, form.name.data
        )
        request.session.delete(self)
        return request.redirect(request.link(new_form))
    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': layout or FormEditorLayout(self, request),
        'form': form,
        'title': site_title,
    }


@OrgApp.form(
    model=FormDefinition,
    template='form.pt', permission=Public,
    form=lambda self, request: self.form_class
)
def handle_defined_form(
    self: FormDefinition,
    request: OrgRequest,
    form: Form,
    layout: FormSubmissionLayout | None = None
) -> RenderData | Response:
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    collection = FormCollection(request.session)

    if not self.current_registration_window:
        spots = 0
        enabled = True
    else:
        spots = 1
        enabled = self.current_registration_window.accepts_submissions(spots)

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending', spots=spots)

        return morepath.redirect(request.link(submission))

    layout = layout or FormSubmissionLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': layout.linkify(self.meta.get('lead')),
        'text': self.text,
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': getattr(self, 'coordinates', Coordinates()),
        'hints': tuple(get_hints(layout, self.current_registration_window)),
        'hints_callout': not enabled,
        'button_text': _('Continue')
    }


@OrgApp.form(
    model=FormCollection,
    name='new', template='form.pt',
    permission=Private, form=get_form_class
)
def handle_new_definition(
    self: FormCollection,
    request: OrgRequest,
    form: FormDefinitionForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        assert form.definition.data is not None

        if self.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_('A form with this name already exists'))
        else:
            definition = self.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
                type='custom'
            )
            form.populate_obj(definition)

            request.success(_('Added a new form'))
            return morepath.redirect(request.link(definition))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.link(self)),
        Link(_('New Form'), request.link(self, name='new'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New Form'),
        'form': form,
        'form_width': 'large',
    }


@OrgApp.form(
    model=FormDefinition,
    template='form.pt', permission=Private,
    form=get_form_class, name='edit'
)
def handle_edit_definition(
    self: FormDefinition,
    request: OrgRequest,
    form: FormDefinitionForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.definition.data is not None
        # why do we exclude definition here? we set it normally right after
        # which is also what populate_obj should be doing
        form.populate_obj(self, exclude={'definition'})
        self.definition = form.definition.data

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    collection = FormCollection(request.session)

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_('Edit'), request.link(self, name='edit'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large',
    }


@OrgApp.view(
    model=FormDefinition,
    request_method='DELETE',
    permission=Private
)
def delete_form_definition(
    self: FormDefinition,
    request: OrgRequest
) -> None:
    """
    With introduction of cancelling submissions over the registration window,
    we encourage the user to use this functionality to cancel all form
    submissions through the ticket system.

    This ensures all submissions are cancelled/denied and the tickets are
    closed.In that case the ticket itself attached to the submission is
    deletable.

    If the customer wants to delete the form directly, we allow it now even
    when there are completed submissions. In each case there is a ticket
    associated with it we might take a snapshot before deleting it.
    """

    request.assert_valid_csrf_token()

    if self.type != 'custom':
        raise exc.HTTPMethodNotAllowed()

    def handle_ticket(submission: FormSubmission) -> None:
        ticket = submission_deletable(submission, request.session)
        if ticket is False:
            raise exc.HTTPMethodNotAllowed()
        if ticket is not True:
            assert request.current_user is not None
            close_ticket(ticket, request.current_user, request)
            ticket.create_snapshot(request)

    def handle_submissions(submissions: Iterable[FormSubmission]) -> None:
        for s in submissions:
            handle_ticket(s)

    FormCollection(request.session).definitions.delete(
        self.name,
        with_submissions=True,
        with_registration_windows=True,
        handle_submissions=handle_submissions
    )


@OrgApp.view(
    model=FormCollection,
    name='formcoder',
    request_method='POST',
    permission=Private
)
def formcoder(self: FormCollection, request: OrgRequest) -> Response:
    """Generate formcode for a new form being created or edited.

    This handles POSTs to e.g. /forms/formcoder, requesting AI support
    from infomaniak and finally returns plain text beeing replaced in the
    form defintion text field.
    """
    token = request.app.infomaniak_api_token
    snippet = request.params.get('snippet', '')
    product_id: str | None = None

    if not snippet:
        return Response(body='Missing prompt', content_type='text/plain')

    if not token:
        log.warning('Formcoder: Infomaniak API token not configured')
        return Response(status='error',
                        body='INFOMANIAK_API_TOKEN_NOT_CONFIGURED',
                        content_type='text/plain')

    # read product id
    url = 'https://api.infomaniak.com/1/ai'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url=url, headers=headers, timeout=5).json()
    if response['result'] == 'success':
        product_id = response['data'][0]['product_id']

    if not product_id:
        log.warning('Formcocder: Could not retrieve product id from Infomaniak API')
        return Response(status='error',
                        body='Could not retrieve product id from Infomaniak API',
                        content_type='text/plain')

    # prompt = (
    #     'Generate a valid onegov.form definition based on https://docs.admin.digital/module/formulare/. '
    #     'Return only the generated form definition as plain text suitable for the definition field.\n\n'
    #     'Snippet:\n' + snippet
    # )
    prompt = (
            'Generate a valid onegovcloud form definition based on https://docs.admin.digital/module/formulare/'
            'syntax. Return only the generated form definition as plain.\n\n'
            'Snippet:\n' + snippet
    )
    # available llms ["mixtral","llama3","granite","mistral24b","mistral3","qwen3","gemma3n"]
    model = 'qwen3'
    url = f'https://api.infomaniak.com/1/ai/{product_id}/openai/chat/completions'
    payload = {
        'model': model,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        log.error('Formcoder: Infomaniak API request failed: %s', e, exc_info=True)
        # does it appear on the ui as not reloaded??
        request.alert(_('Failed to generate form code: {error}', mapping={'error': str(e)}))
        return Response(body=f'Infomaniak API request failed with \'{e}\'', content_type='text/plain')

    if not response.ok:
        log.error('Formcoder: Failed to generate form code. API error: %s, %s',
                  response.status_code, response.text)
        # does it appear on the ui as not reloaded??
        request.alert(_('Formcoder: Failed to generate form code. API error {status}',
                        mapping={'status': response.status_code}))
        return Response(status='error',
                        body='Formcoder: Failed to generate form code. API error {text}'.format(status=response.text),
                        content_type='text/plain')

    generated = ''
    try:
        data = response.json()
        print('*** response data: ' + str(data))
        if isinstance(data, dict):
            if 'choices' in data and data['choices']:
                choice = data['choices'][0]
                if isinstance(choice, dict):
                    if 'message' in choice and isinstance(choice['message'], dict) and 'content' in choice['message']:
                        generated = choice['message']['content']
    except ValueError:
        pass

    return Response(body=generated, content_type='text/plain')

""" Renders and handles defined forms, turning them into submissions. """

import base64
import morepath

from onegov.core.security import Public, Private
from onegov.form import (
    FormCollection,
    FormDefinition,
    FormSubmissionFile,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import FormSubmissionLayout


@TownApp.form(model=FormDefinition, form=lambda e: e.form_class,
              template='form.pt', permission=Public)
def handle_defined_form(self, request, form):
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    collection = FormCollection(request.app.session())

    if request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending')

        return morepath.redirect(request.link(submission))

    return {
        'layout': FormSubmissionLayout(self, request),
        'title': self.title,
        'form': form,
        'definition': self,
        'form_width': 'small',
        'lead': self.meta.get('lead'),
        'text': self.content.get('text')
    }


@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='GET')
@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='POST')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='GET')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='POST')
def handle_pending_submission(self, request):
    """ Renders a pending submission, takes it's input and allows the
    user to turn the submission into a complete submission, once all data
    is valid.

    """
    collection = FormCollection(request.app.session())

    form = request.get_form(self.form_class, data=self.data)
    form.action = request.link(self)
    form.validate()

    if not request.POST:
        form.ignore_csrf_error()
    else:
        collection.submissions.update(self, form)

    completable = not form.errors and 'edit' not in request.GET

    return {
        'layout': FormSubmissionLayout(self, request),
        'title': self.form.title,
        'form': form,
        'completable': completable,
        'edit_link': request.link(self) + '?edit',
        'complete_link': request.link(self, 'complete'),
        'is_pending': self.state == 'pending',
        'readonly': 'readonly' in request.GET
    }


@TownApp.view(model=PendingFormSubmission, name='complete',
              permission=Public, request_method='POST')
@TownApp.view(model=CompleteFormSubmission, name='complete',
              permission=Private, request_method='POST')
def handle_complete_submission(self, request):
    form = request.get_form(self.form_class, data=self.data)

    # we're not really using a csrf protected form here (the complete form
    # button is basically just there so we can use a POST instead of a GET)
    form.validate()
    form.ignore_csrf_error()

    if form.errors:
        return morepath.redirect(request.link(self))
    else:
        if self.state == 'complete':
            self.data.changed()  # trigger updates
            request.success(_(u"Your changes were saved"))

            return morepath.redirect(request.link(
                FormCollection(request.app.session()).scoped_submissions(
                    self.name, ensure_existance=False)
            ))
        else:
            collection = FormCollection(request.app.session())
            collection.submissions.complete_submission(self)

            # TODO Show a new page with the transaction id and a thank you
            request.success(_(u"Thank you for your submission"))

            return morepath.redirect(request.link(collection))


@TownApp.view(model=FormSubmissionFile, permission=Private)
def view_form_submission_file(self, request):
    response = morepath.Response(base64.b64decode(self.filedata))
    response.content_type = self.submission_data['mimetype']
    response.content_encoding = 'gzip'

    return response


@TownApp.view(model=CompleteFormSubmission, request_method='DELETE',
              permission=Private)
def delete_form_submission(self, request):
    request.assert_valid_csrf_token()
    FormCollection(request.app.session()).submissions.delete(self)

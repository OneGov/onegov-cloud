""" Renders and handles defined forms, turning them into submissions. """

import morepath

from onegov.core.security import Public, Private
from onegov.ticket import TicketCollection
from onegov.form import (
    FormCollection,
    FormDefinition,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.org import _, OrgApp
from onegov.org.layout import FormSubmissionLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.org.models import TicketMessage
from onegov.pay import Price
from purl import URL


def copy_query(request, url, fields):
    url = URL(url)

    for field in fields:
        if field in request.GET:
            url = url.query_param(field, request.GET[field])

    return url.as_string()


def get_price(request, form, submission):
    total = form.total()

    if 'price' in submission.meta:
        if total is not None:
            total += Price(**submission.meta['price'])
        else:
            total = Price(**submission.meta['price'])

    return request.app.adjust_price(total)


@OrgApp.form(model=FormDefinition, template='form.pt', permission=Public,
             form=lambda self, request: self.form_class)
def handle_defined_form(self, request, form):
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    collection = FormCollection(request.session)

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
        'text': self.content.get('text'),
        'people': self.people,
        'contact': self.contact_html,
        'coordinates': self.coordinates
    }


@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='GET')
@OrgApp.html(model=PendingFormSubmission, template='submission.pt',
             permission=Public, request_method='POST')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='GET')
@OrgApp.html(model=CompleteFormSubmission, template='submission.pt',
             permission=Private, request_method='POST')
def handle_pending_submission(self, request):
    """ Renders a pending submission, takes it's input and allows the
    user to turn the submission into a complete submission, once all data
    is valid.

    This view has two states, a completeable state where the form values
    are displayed without a form and an edit state, where a form is rendered
    to change the values.

    Takes the following query parameters for customization::

        * ``edit`` render the view in the edit state
        * ``return-to`` the view redirects to this url once complete
        * ``title`` a custom title (required if external submission)
        * ``quiet`` no success messages are rendered if present

    """
    collection = FormCollection(request.session)

    form = request.get_form(self.form_class, data=self.data)
    form.action = request.link(self)

    if 'edit' not in request.GET:
        form.validate()

    if not request.POST:
        form.ignore_csrf_error()
    elif not form.errors:
        collection.submissions.update(self, form)

    completable = not form.errors and 'edit' not in request.GET

    if completable and 'return-to' in request.GET:

        if 'quiet' not in request.GET:
            request.success(_("Your changes were saved"))

        # the default url should actually never be called
        return request.redirect(request.url)

    if 'title' in request.GET:
        title = request.GET['title']
    else:
        title = self.form.title

    price = get_price(request, form, self)

    # retain some parameters in links (the rest throw away)
    form.action = copy_query(
        request, form.action, ('return-to', 'title', 'quiet'))

    edit_link = URL(copy_query(
        request, request.link(self), ('title', )))

    # the edit link always points to the editable state
    edit_link = edit_link.query_param('edit', '')
    edit_link = edit_link.as_string()

    return {
        'layout': FormSubmissionLayout(self, request, title),
        'title': title,
        'form': form,
        'completable': completable,
        'edit_link': edit_link,
        'complete_link': request.link(self, 'complete'),
        'model': self,
        'price': price,
        'checkout_button': price and request.app.checkout_button(
            button_label=request.translate(_("Pay Online and Complete")),
            title=title,
            price=price,
            email=self.email or self.get_email_field_data(form),
            locale=request.locale
        )
    }


@OrgApp.view(model=PendingFormSubmission, name='complete',
             permission=Public, request_method='POST')
@OrgApp.view(model=CompleteFormSubmission, name='complete',
             permission=Private, request_method='POST')
def handle_complete_submission(self, request):
    form = request.get_form(self.form_class)
    form.process(data=self.data)

    # we're not really using a csrf protected form here (the complete form
    # button is basically just there so we can use a POST instead of a GET)
    form.validate()
    form.ignore_csrf_error()

    if form.errors:
        return morepath.redirect(request.link(self))
    else:
        if self.state == 'complete':
            self.data.changed()  # trigger updates
            request.success(_("Your changes were saved"))

            return morepath.redirect(request.link(
                FormCollection(request.session).scoped_submissions(
                    self.name, ensure_existance=False)
            ))
        else:
            provider = request.app.default_payment_provider
            token = request.params.get('payment_token')

            price = get_price(request, form, self)
            payment = self.process_payment(price, provider, token)

            if not payment:
                request.alert(_("Your payment could not be processed"))
                return morepath.redirect(request.link(self))
            elif payment is not True:
                self.payment = payment

            collection = FormCollection(request.session)
            collection.submissions.complete_submission(self)

            # make sure accessing the submission doesn't flush it, because
            # it uses sqlalchemy utils observe, which doesn't like premature
            # flushing at all
            with collection.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code=self.meta.get('handler_code', 'FRM'),
                    handler_id=self.id.hex
                )
                TicketMessage.create(ticket, request, 'opened')

            if self.email != request.current_username:
                show_submission = request.params.get('send_by_email') == 'yes'

                send_transactional_html_mail(
                    request=request,
                    template='mail_ticket_opened.pt',
                    subject=_("A ticket has been opened"),
                    receivers=(self.email, ),
                    content={
                        'model': ticket,
                        'form': form,
                        'show_submission': show_submission
                    }
                )

            request.success(_("Thank you for your submission!"))

            return morepath.redirect(request.link(ticket, 'status'))

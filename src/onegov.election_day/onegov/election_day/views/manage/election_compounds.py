from morepath import redirect
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.forms import ElectionCompoundForm
from onegov.election_day.layouts import ManageElectionCompoundsLayout


@ElectionDayApp.manage_html(
    model=ElectionCompoundCollection,
    template='manage/election_compounds.pt'
)
def view_election_compounds(self, request):
    """ View a list of all election compoundss. """

    return {
        'layout': ManageElectionCompoundsLayout(self, request),
        'title': _("Election compounds"),
        'groups': groupbylist(self.batch, key=lambda items: items.date),
        'new_election_compound': request.link(self, 'new-election-compound')
    }


@ElectionDayApp.manage_form(
    model=ElectionCompoundCollection,
    name='new-election-compound',
    form=ElectionCompoundForm
)
def create_election_compound(self, request, form):
    """ Create a new election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    # todo:
    # archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        session = request.app.session()
        election_compound = ElectionCompound()
        form.update_model(election_compound)
        session.add(election_compound)
        # todo: use archive instead of adding it directly
        # archive.add(election_compound, request)
        request.message(_("Election compound added."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New election compound"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='edit',
    form=ElectionCompoundForm
)
def edit_election_compound(self, request, form):
    """ Edit an existing election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    # todo:
    # archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        form.update_model(self)
        # todo: ?
        # archive.update(self, request)
        request.message(_("Election compound modified."), 'success')
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit election compound"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='delete'
)
def delete_election_compound(self, request, form):
    """ Delete an existing election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    # toodo:
    # archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        # todo: use archive instead of deleting it directly
        request.app.session().delete(self)
        # archive.delete(self, request)

        request.message(_("Election compound deleted."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Delete election compound"),
        'button_text': _("Delete election compound"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }

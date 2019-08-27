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
        'title': _("Compounds of elections"),
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
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        election_compound = ElectionCompound()
        form.update_model(election_compound)
        archive.add(election_compound, request)
        request.message(_("Compound added."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New compound"),
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
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        request.message(_("Compound modified."), 'success')
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit compound"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='clear'
)
def clear_election_compound(self, request, form):
    """ Clear the results of an election ompound. """

    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.clear(self, request)
        request.message(_("Results deleted."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to clear all party results of "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Clear results"),
        'button_text': _("Clear results"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='delete'
)
def delete_election_compound(self, request, form):
    """ Delete an existing election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.delete(self, request)

        request.message(_("Compound deleted."), 'success')
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
        'subtitle': _("Delete compound"),
        'button_text': _("Delete compound"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }

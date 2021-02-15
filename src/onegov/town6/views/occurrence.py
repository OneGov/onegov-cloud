""" The onegov org collection of images uploaded to the site. """

from onegov.core.security import Public, Private

from onegov.event import Occurrence, OccurrenceCollection
from onegov.org.views.occurrence import view_occurrences, view_occurrence, \
    export_occurrences
from onegov.town6 import _, TownApp
from onegov.org.forms import ExportForm


@TownApp.html(model=OccurrenceCollection, template='occurrences.pt',
             permission=Public)
def town_view_occurrences(self, request):
    return view_occurrences(self, request)


@TownApp.html(model=Occurrence, template='occurrence.pt', permission=Public)
def town_view_occurrence(self, request):
    return view_occurrence(self, request)


@TownApp.form(model=OccurrenceCollection, name='export', permission=Private,
             form=ExportForm, template='export.pt')
def town_export_occurrences(self, request, form):
    return export_occurrences(self, request, form)

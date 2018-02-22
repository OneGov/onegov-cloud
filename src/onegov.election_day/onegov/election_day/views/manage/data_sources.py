""" The manage subscription views. """

import morepath

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.forms import DataSourceForm
from onegov.election_day.forms import DataSourceItemForm
from onegov.election_day.layouts import ManageDataSourceItemsLayout
from onegov.election_day.layouts import ManageDataSourcesLayout
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models.data_source import UPLOAD_TYPE_LABELS
from uuid import uuid4


@ElectionDayApp.manage_html(
    model=DataSourceCollection,
    template='manage/data_sources.pt'
)
def view_data_sources(self, request):

    """ View all data sources as a list. """

    return {
        'layout': ManageDataSourcesLayout(self, request),
        'title': _("Data sources"),
        'data_sources': self.batch,
        'new_source': request.link(self, 'new-source'),
        'labels': dict(UPLOAD_TYPE_LABELS)
    }


@ElectionDayApp.manage_form(
    model=DataSourceCollection,
    name='new-source',
    form=DataSourceForm
)
def create_data_source(self, request, form):

    """ Create a new data source. """

    layout = ManageDataSourcesLayout(self, request)

    if form.submitted(request):
        data_source = DataSource()
        form.update_model(data_source)
        self.add(data_source)
        layout = ManageDataSourceItemsLayout(data_source, request)
        request.message(_("Data source added."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New data source"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_html(
    model=DataSource,
    name='manage'
)
def manage_data_source(self, request):

    """ Manage the data source.

    Redirect to the list of data source items.

    """

    layout = ManageDataSourceItemsLayout(self, request)
    return morepath.redirect(layout.manage_model_link)


@ElectionDayApp.manage_form(
    model=DataSource,
    name='generate-token'
)
def generate_data_source_token(self, request, form):

    """ Regenerate a new token for the data source. """

    layout = ManageDataSourcesLayout(self, request)

    if form.submitted(request):
        self.token = uuid4()
        request.message(_("Token regenerated."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _('Do you really want to regenerate the token?'),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Regenerate token"),
        'button_text': _("Regenerate token"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=DataSource,
    name='delete'
)
def delete_data_source(self, request, form):

    """ Delete the data source item. """

    layout = ManageDataSourcesLayout(self, request)

    if form.submitted(request):
        data_sources = DataSourceCollection(request.session)
        data_sources.delete(self)
        request.message(_("Data source deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.name
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete data source"),
        'button_text': _("Delete data source"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_html(
    model=DataSourceItemCollection,
    template='manage/data_source_items.pt'
)
def view_data_source_items(self, request):

    """ View all data source items as a list. """

    return {
        'layout': ManageDataSourceItemsLayout(self, request),
        'title': _("Mappings"),
        'items': self.batch,
        'item_name': self.source.label,
        'source': self.source,
        'new_item': request.link(self, 'new-item')
    }


@ElectionDayApp.manage_form(
    model=DataSourceItemCollection,
    name='new-item',
    form=DataSourceItemForm
)
def create_data_source_item(self, request, form):

    """ Create a new data source item. """

    layout = ManageDataSourceItemsLayout(self, request)

    form.populate(self.source)

    if form.submitted(request):
        data_source_item = DataSourceItem()
        form.update_model(data_source_item)
        self.add(data_source_item)
        request.message(_("Mapping added."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'callout': form.callout,
        'title': _("New mapping"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=DataSourceItem,
    name='edit',
    form=DataSourceItemForm
)
def edit_data_source_item(self, request, form):

    """ Edit a data source item. """

    layout = ManageDataSourceItemsLayout(self.source, request)

    form.populate(self.source)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Mapping modified."), 'success')
        return morepath.redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Edit mapping"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=DataSourceItem,
    name='delete'
)
def delete_data_source_item(self, request, form):

    """ Delete the data source item. """

    layout = ManageDataSourceItemsLayout(self.source, request)

    if form.submitted(request):
        data_source_items = DataSourceItemCollection(request.session)
        data_source_items.delete(self)
        request.message(_("Mapping deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.name
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.name,
        'subtitle': _("Delete mapping"),
        'button_text': _("Delete mapping"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }

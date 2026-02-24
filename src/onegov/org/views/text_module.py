from __future__ import annotations

from morepath import redirect
from onegov.chat import TextModule
from onegov.chat import TextModuleCollection
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.forms import TextModuleForm
from onegov.org.layout import TextModuleLayout
from onegov.org.layout import TextModulesLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.html(
    model=TextModuleCollection,
    template='text_modules.pt',
    permission=Private
)
def view_text_modules(
    self: TextModuleCollection,
    request: OrgRequest,
    layout: TextModulesLayout | None = None
) -> RenderData:

    layout = layout or TextModulesLayout(self, request)

    return {
        'title': _('Text modules'),
        'layout': layout,
        'text_modules': self.query().all(),
    }


@OrgApp.form(
    model=TextModuleCollection,
    name='add',
    permission=Private,
    template='form.pt',
    form=TextModuleForm
)
def add_text_module(
    self: TextModuleCollection,
    request: OrgRequest,
    form: TextModuleForm,
    layout: TextModulesLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        text_module = self.add(
            name=form.name.data,
            text=form.text.data
        )
        form.populate_obj(text_module)
        request.success(_('Added a new text module'))
        return redirect(request.link(self))

    layout = layout or TextModulesLayout(self, request)
    layout.breadcrumbs.append(Link(_('New text module'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New text module'),
        'form': form
    }


@OrgApp.html(
    model=TextModule,
    template='text_module.pt',
    permission=Private
)
def view_text_module(
    self: TextModule,
    request: OrgRequest,
    layout: TextModuleLayout | None = None
) -> RenderData:

    layout = layout or TextModuleLayout(self, request)

    return {
        'title': self.name,
        'layout': layout
    }


@OrgApp.form(
    model=TextModule,
    name='edit',
    permission=Private,
    template='form.pt',
    form=TextModuleForm
)
def edit_text_module(
    self: TextModule,
    request: OrgRequest,
    form: TextModuleForm,
    layout: TextModuleLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return redirect(request.class_link(TextModuleCollection))

    if not form.errors:
        form.process(obj=self)

    layout = layout or TextModuleLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit text module'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('Edit text module'),
        'form': form
    }


@OrgApp.view(
    model=TextModule,
    permission=Private,
    request_method='DELETE'
)
def delete_text_module(self: TextModule, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    request.session.delete(self)
    request.success(_('The text module was deleted'))

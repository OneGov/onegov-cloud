from __future__ import annotations

from json import dumps
from markupsafe import Markup
from random import choice
from wtforms.widgets import HiddenInput


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.quill.fields import QuillField


HEADINGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
LISTS = ['ol', 'ul']
TAGS = ['strong', 'em', 'a', *HEADINGS, *LISTS, 'blockquote']


class QuillInput(HiddenInput):
    """
    Renders the text content as hidden input and adds a container for the
    editor.


    """

    toolbar: list[str | dict[str, int | str]]

    def __init__(
        self,
        *,
        tags: Sequence[str] | None = None,
        **kwargs: Any
    ):
        if tags is None:
            tags = TAGS
        else:
            tags = list(set(tags) & set(TAGS))

        super().__init__(**kwargs)

        self.id = ''.join(choice('abcdefghi') for i in range(8))  # nosec B311

        self.formats = []
        if 'strong' in tags:
            self.formats.append('bold')
        if 'em' in tags:
            self.formats.append('italic')
        if 'a' in tags:
            self.formats.append('link')
        if set(tags) & set(HEADINGS):
            self.formats.append('header')
        if set(tags) & set(LISTS):
            self.formats.append('list')
        if 'blockquote' in tags:
            self.formats.append('blockquote')

        self.toolbar = []
        if 'strong' in tags:
            self.toolbar.append('bold')
        if 'em' in tags:
            self.toolbar.append('italic')
        if 'a' in tags:
            self.toolbar.append('link')
        if 'h1' in tags:
            self.toolbar.append({'header': 1})
        if 'h2' in tags:
            self.toolbar.append({'header': 2})
        if 'h3' in tags:
            self.toolbar.append({'header': 3})
        if 'h4' in tags:
            self.toolbar.append({'header': 4})
        if 'h5' in tags:
            self.toolbar.append({'header': 5})
        if 'h6' in tags:
            self.toolbar.append({'header': 6})
        if 'ol' in tags:
            self.toolbar.append({'list': 'ordered'})
        if 'ul' in tags:
            self.toolbar.append({'list': 'bullet'})
        if 'blockquote' in tags:
            self.toolbar.append('blockquote')

    def __call__(
        self,
        field: QuillField,  # type:ignore[override]
        **kwargs: Any
    ) -> Markup:

        input_id = f'quill-input-{self.id}'
        kwargs['id'] = input_id

        return Markup("""
            <div style="position:relative" class="quill-widget"
                data-input-id="{input_id}"
                data-container-id="{container_id}"
                data-scroll-container-id="{scroll_container_id}"
                data-formats='{formats}'
                data-toolbar='[{toolbar}]'
                >
                <div class="scrolling-container" id="{scroll_container_id}">
                  <div class="quill-container" id="{container_id}"></div>
                </div>
            </div>
            {input}
        """).format(
            input_id=input_id,
            container_id=f'quill-container-{self.id}',
            scroll_container_id=f'scrolling-container-{self.id}',
            input=super().__call__(field, **kwargs),
            # FIXME: we should probably escape the json dump, but then we
            #        need to adjust the tests to detect the &quot; for the
            #        strings inside the JSON. (The &quot; will be turned back
            #        into `"` in javascript, so there's no harm to it)
            formats=Markup(dumps(self.formats)),  # nosec: B704
            toolbar=Markup(dumps(self.toolbar)),  # nosec: B704
        )

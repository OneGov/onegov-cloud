from random import choice
from wtforms.widgets import HiddenInput
from wtforms.widgets.core import HTMLString


TAGS = ('strong', 'em', 'ol', 'ul')


class QuillInput(HiddenInput):
    """
    Renders the text content as hidden input and adds a container for the
    editor.


    """

    def __init__(self, **kwargs):
        tags = list(set(kwargs.pop('tags', TAGS)) & set(TAGS))

        super(QuillInput, self).__init__(**kwargs)

        id = ''.join(choice('abcdefghi') for i in range(8))
        self.container_id = 'quill-container-{}'.format(id)
        self.input_id = 'quill-input-{}'.format(id)

        self.formats = []
        if 'strong' in tags:
            self.formats.append("'bold'")
        if 'em' in tags:
            self.formats.append("'italic'")
        if 'ol' in tags or 'ul' in tags:
            self.formats.append("'list'")

        self.toolbar = []
        if 'strong' in tags:
            self.toolbar.append("'bold'")
        if 'em' in tags:
            self.toolbar.append("'italic'")
        if 'ol' in tags:
            self.toolbar.append("{'list': 'ordered'}")
        if 'ul' in tags:
            self.toolbar.append("{'list': 'bullet'}")

    def __call__(self, field, **kwargs):
        kwargs['id'] = self.input_id
        input = super(QuillInput, self).__call__(field, **kwargs)

        return HTMLString("""
                <div class="quill-container" id="{container_id}"></div>
                <script>
                    window.addEventListener('load', function () {{
                        var input = document.getElementById('{input_id}');
                        var quill = new Quill('#{container_id}', {{
                            formats: [{formats}],
                            modules: {{toolbar: [{toolbar}]}},
                            theme: 'snow'
                        }});
                        quill.clipboard.dangerouslyPasteHTML(input.value);
                        quill.on('text-change', function() {{
                            input.value = quill.root.innerHTML
                        }});
                    }});
                </script>
                {input}
        """.format(
            container_id=self.container_id,
            input_id=self.input_id,
            formats=', '.join(self.formats),
            toolbar=', '.join(self.toolbar),
            input=input
        ))

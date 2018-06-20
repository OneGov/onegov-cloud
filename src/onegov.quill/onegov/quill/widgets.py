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
        self.placeholders = kwargs.pop('placeholders', {})
        self.placeholder_label = kwargs.pop('placeholder_label', 'Snippets')

        super(QuillInput, self).__init__(**kwargs)

        self.id = ''.join(choice('abcdefghi') for i in range(8))

        self.formats = []
        if 'strong' in tags:
            self.formats.append("'bold'")
        if 'em' in tags:
            self.formats.append("'italic'")
        if 'ol' in tags or 'ul' in tags:
            self.formats.append("'list'")
        if self.placeholders:
            self.formats.append("'placeholder'")

        self.toolbar = []
        if 'strong' in tags:
            self.toolbar.append("'bold'")
        if 'em' in tags:
            self.toolbar.append("'italic'")
        if 'ol' in tags:
            self.toolbar.append("{'list': 'ordered'}")
        if 'ul' in tags:
            self.toolbar.append("{'list': 'bullet'}")
        if self.placeholders:
            options = [f"'{key}'" for key in self.placeholders]
            options = ', '.join(options)
            self.toolbar.append(f"{{'placeholder': [{options}]}}")

    def __call__(self, field, **kwargs):
        input_id = f'quill-input-{self.id}'
        kwargs['id'] = input_id
        input = super(QuillInput, self).__call__(field, **kwargs)

        container_id = f'quill-container-{self.id}'
        formats = ', '.join(self.formats)
        toolbar = ', '.join(self.toolbar)
        placeholders = [
            f"{{id: '{key}', label: '{value}'}}"
            for key, value in self.placeholders.items()
        ]
        placeholders = ', '.join(placeholders)

        return HTMLString(f"""
            <div class="quill-container" id="{container_id}"></div>
            <script>
                window.addEventListener('load', function () {{
                    Quill.register(
                        'modules/placeholder',
                        PlaceholderModule.default(Quill)
                    )
                    var input = document.getElementById('{input_id}');
                    var quill = new Quill('#{container_id}', {{
                        formats: [{formats}],
                        modules: {{
                            toolbar: [{toolbar}],
                            placeholder: {{
                                delimiters: ['', ''],
                                placeholders: [{placeholders}]
                            }}
                        }},
                        theme: 'snow'
                    }});
                    quill.clipboard.dangerouslyPasteHTML(input.value);
                    quill.on('text-change', function() {{
                        input.value = quill.root.innerHTML
                    }});
                    Array.prototype.slice.call(
                        document.querySelectorAll(
                            '.ql-placeholder .ql-picker-item'
                        )
                    ).forEach(item => item.textContent = item.dataset.value);
                    var label = document.querySelector(
                        '.ql-placeholder .ql-picker-label'
                    );
                    if (label) {{
                        label.innerHTML = '{self.placeholder_label}';
                    }}
                }});
            </script>
            {input}
        """)

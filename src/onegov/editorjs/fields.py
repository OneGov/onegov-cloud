from base64 import b64encode, b64decode
from wtforms.fields import StringField
from onegov.core.custom import json
from onegov.editorjs.models import EditorJsDBField


class EditorJsField(StringField):
    def __init__(self, *args, **kwargs):
        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editorjs'

        super().__init__(*args, **kwargs)
        self.data = getattr(self, 'data', EditorJsDBField())

    def _value(self):
        text = json.dumps(self.data) or '{}'
        text = b64encode(text.encode('utf-8'))
        text = text.decode('utf-8')

        return text

    def process_data(self, value):
        if isinstance(value, dict):
            self.data = EditorJsDBField(**value)
        else:
            self.data = value

    def populate_obj(self, obj, name):
        setattr(obj, name, self.data)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            text = b64decode(valuelist[0])
            text = text.decode('utf-8')
            self.data = json.loads(text)
        else:
            self.data = EditorJsField()

        if not isinstance(self.data, EditorJsDBField):
            self.data = EditorJsDBField()

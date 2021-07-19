import json
from base64 import b64encode

from onegov.editorjs.fields import EditorJsField
from onegov.form import Form

header_sample = {
    "type": "header",
    "data": {
        "text": "Editor.js ÄÖ & // ",
        "level": 2
    }
}

list_sample = {
    "type": "list",
    "data": {
        "style": "unordered",
        "items": [
            "It is a block-styled editor",
            "It returns clean data output in JSON",
            "Designed to be extendable and pluggable with a simple API"
        ]
    }
}

paragraph_exapmple = {
    "type": "paragraph",
    "data": {
        "text": "Workspace in classic editors is made of a single contenteditable "
                "element, used to create different HTML markups. "
                "Editor.js <mark class=\"cdx-marker\">workspace consists of "
                "separate Blocks: paragraphs, headings, images, lists, quotes, "
                "etc</mark>. Each of them is an independent contenteditable "
                "element (or more complex structure) provided by Plugin and "
                "united by Editor's Core."
    }
}


def editor_js_form_field():
    form = Form()
    field = EditorJsField().bind(form, 'text')
    assert not field.data
    assert field.data.blocks == []
    assert field.data.time is None
    assert field.data.version is None

    field.process_formdata([b64encode(
        json.dumps(header_sample).encode('utf-8')
    ).decode('utf-8')])
    assert field.data.blocks[0] == header_sample

    field.process_data(list_sample)
    assert field.data.blocks[0] == list_sample


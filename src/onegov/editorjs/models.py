from onegov.core.custom import json
from onegov.core.orm.mixins import dict_property


def editorjs_dict_property_factory(attribute):
    def factory(*args, **kwargs):
        prop = dict_property(attribute, *args, **kwargs)

        def get_editor_js(self):
            return getattr(self, attribute).get(prop.key) or EditorJsDBField()

        def set_editor_js(self, value):
            field = getattr(self, attribute)
            field[prop.key] = value or EditorJsDBField()
            setattr(self, attribute, field)

        prop.custom_getter = get_editor_js
        prop.custom_setter = set_editor_js
        return prop

    return factory


editorjs_content = editorjs_dict_property_factory('content')
editorjs_meta = editorjs_dict_property_factory('meta')


class EditorJsDBField(json.Serializable, keys=('time', 'blocks', 'version')):
    """ Represents data of an editor js instance.
    """

    __slots__ = ('time', 'blocks', 'version')

    def __init__(self, time=None, blocks=None, version=None):
        self.time = time
        self.blocks = blocks or []
        self.version = version

    def __bool__(self):
        return self.blocks and True or False

    def __eq__(self, other):
        if not isinstance(other, EditorJsDBField):
            return False

        return all(
            (self.version == other.version, self.blocks == other.blocks)
        )

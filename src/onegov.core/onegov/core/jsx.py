""" Integrates a JSX filter for webassets. """

from webassets.filter import Filter, register_filter


class JsxFilter(Filter):
    name = 'jsx'

    def setup(self):
        from react import jsx
        self.transformer = jsx.JSXTransformer()

    def input(self, _in, out, **kwargs):
        out.write(self.transformer.transform_string(_in.read()))


register_filter(JsxFilter)

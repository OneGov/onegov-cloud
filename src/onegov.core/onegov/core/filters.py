""" Extra webasset filters. """

from webassets.filter import Filter, register_filter
from webassets.filter.datauri import CSSDataUri, CSSUrlRewriter


class JsxFilter(Filter):
    name = 'jsx'

    def setup(self):
        from react import jsx
        self.transformer = jsx.JSXTransformer()

    def input(self, _in, out, **kwargs):
        out.write(self.transformer.transform_string(_in.read()))


register_filter(JsxFilter)


class DataUriFilter(CSSDataUri):
    """ Overrides the default datauri filter to work around this issue:

    https://github.com/miracle2k/webassets/issues/387

    """

    name = 'datauri'

    def input(self, _in, out, **kw):
        self.keywords = kw

        self.source_path = self.keywords['source_path']
        self.output_path = self.keywords['output_path']

        return super(CSSUrlRewriter, self).input(_in, out, **kw)

    @property
    def source_url(self):
        return self.ctx.resolver.resolve_source_to_url(
            self.ctx, self.keywords['source_path'], self.keywords['source'])

    @property
    def output_url(self):
        return self.ctx.resolver.resolve_output_to_url(
            self.ctx, self.keywords['output'])


register_filter(DataUriFilter)

""" Extra webasset filters. """
import os
import rcssmin

from webassets.filter import Filter, register_filter
from webassets.filter.datauri import CSSDataUri, CSSUrlRewriter
from dukpy.webassets import BabelJSX
from dukpy import jsx_compile


class JsxFilter(BabelJSX):
    """
    DukPy is a simple javascript interpreter for Python built on top of
    duktape engine without any external dependency.

    Note: let is not supported by the duktape engine,
    see https://github.com/amol-/dukpy/issues/47.
    """
    name = 'jsx'

    babel_options = {'minified': True}

    def input(self, _in, out, **kwargs):
        """kwargs are actually babel options"""
        options = self.babel_options.copy()
        source_path = kwargs.get('source_path')
        if source_path:
            options['filename'] = os.path.basename(source_path)

        if self.loader == 'systemjs':
            options['plugins'] = ['transform-es2015-modules-systemjs']
        elif self.loader == 'umd':
            options['plugins'] = ['transform-es2015-modules-umd']
        out.write(self.transformer(_in.read(), **options))

    def setup(self):
        self.transformer = jsx_compile


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


class RCSSMinFilter(Filter):
    """ Adds the rcssmin filter (not yet included in webassets) """

    name = 'custom-rcssmin'

    def setup(self):
        self.rcssmin = rcssmin

    def output(self, _in, out, **kw):
        out.write(self.rcssmin.cssmin(_in.read()))


register_filter(RCSSMinFilter)

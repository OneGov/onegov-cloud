""" Extra webasset filters. """
from __future__ import annotations

import os
import rcssmin  # type:ignore[import-untyped]

from webassets.filter import Filter, register_filter
from webassets.filter.datauri import (
    CSSDataUri, CSSUrlRewriter)
from dukpy.webassets import BabelJSX  # type:ignore[import-untyped]
from dukpy import jsx_compile  # type:ignore[import-untyped]


from typing import Any, IO


class JsxFilter(BabelJSX):  # type:ignore[misc]
    """
    DukPy is a simple javascript interpreter for Python built on top of
    duktape engine without any external dependency.

    Note: let is not supported by the duktape engine,
    see https://github.com/amol-/dukpy/issues/47.
    """
    name = 'jsx'

    babel_options: dict[str, Any] = {'minified': True}

    def input(
        self,
        _in: IO[str],
        out: IO[str],
        *,
        source_path: str | None = None,
        **kwargs: Any
    ) -> None:
        """:param kwargs: are actually babel options"""
        options = self.babel_options.copy()
        if source_path:
            options['filename'] = os.path.basename(source_path)

        if self.loader == 'systemjs':
            options['plugins'] = ['transform-es2015-modules-systemjs']
        elif self.loader == 'umd':
            options['plugins'] = ['transform-es2015-modules-umd']
        out.write(self.transformer(_in.read(), **options))

    def setup(self) -> None:
        self.transformer = jsx_compile


register_filter(JsxFilter)  # type:ignore[no-untyped-call]


class DataUriFilter(CSSDataUri):
    """ Overrides the default datauri filter to work around this issue:

    https://github.com/miracle2k/webassets/issues/387

    """

    name = 'datauri'

    def input(self, _in: IO[str], out: IO[str], **kw: Any) -> None:
        self.keywords = kw

        self.source_path = self.keywords['source_path']
        self.output_path = self.keywords['output_path']

        return super(CSSUrlRewriter, self).input(_in, out, **kw)  # type:ignore[no-untyped-call]

    @property
    def source_url(self) -> str:
        return self.ctx.resolver.resolve_source_to_url(  # type:ignore[union-attr]
            self.ctx, self.keywords['source_path'], self.keywords['source'])

    @property
    def output_url(self) -> str:
        return self.ctx.resolver.resolve_output_to_url(  # type:ignore[union-attr]
            self.ctx, self.keywords['output'])


register_filter(DataUriFilter)  # type:ignore[no-untyped-call]


class RCSSMinFilter(Filter):
    """ Adds the rcssmin filter (not yet included in webassets) """

    name = 'custom-rcssmin'   # type:ignore[assignment]

    def setup(self) -> None:
        self.rcssmin = rcssmin

    def output(self, _in: IO[str], out: IO[str], **kw: Any) -> None:
        out.write(self.rcssmin.cssmin(_in.read()))


register_filter(RCSSMinFilter)  # type:ignore[no-untyped-call]

""" Provides the building stones for adding analytics to a site.

An analytics provider can provide both user- and application-facing
configuration

"""
from __future__ import annotations

from abc import abstractmethod, ABCMeta


from typing import Any, ClassVar, Self, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup

    from .types import RenderData

    AnyRequest: TypeAlias = Any


class AnalyticsProvider(metaclass=ABCMeta):
    """ Base class and registry for analytics providers. """

    __slots__ = ('configuration',)

    if TYPE_CHECKING:
        # forward declare for type checking
        name: ClassVar[str]
        title: ClassVar[str]

    def __init__(self, **configuration: Any) -> None:
        self.configuration = configuration

    @property
    def display_name(self) -> str:
        return self.title

    def url(self, request: AnyRequest) -> str | None:
        return None

    @property
    @abstractmethod
    def template(self) -> Markup:
        raise NotImplementedError()

    @classmethod
    def configure(cls, **kwargs: Any) -> Self | None:
        """ This function gets called with the per-provider configuration
        defined in onegov.yml. Analytics providers may optionally
        access these values.

        The return value is either a provider instance, or ``None`` if the
        provider is not available.

        """
        return cls(**kwargs)

    @abstractmethod
    def template_variables(
        self,
        request: AnyRequest
    ) -> RenderData | None:
        """ Returns the necessary variables for formatting the template
        or ``None`` if the analytics can't be rendered. """

    def code(self, request: AnyRequest) -> Markup | None:
        """ This function gets called for every request where this provider
        is active and returns the necessary html embed. """
        variables = self.template_variables(request)
        if variables is None:
            return None
        return self.template.format(**variables)

from typing import Final

from .template import Template as Template, expand as expand
from .url import URL as URL

__version__: Final[str]
__all__ = ["URL", "expand", "Template"]

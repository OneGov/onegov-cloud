from __future__ import annotations

# Ensure that the top-level 'onegov' package works reliably across different
# tooling/environments (e.g. IDEs like PyCharm) by explicitly declaring it as
# a namespace package. This complements implicit namespace packages (PEP 420)
# and avoids ModuleNotFoundError issues when sys.path handling differs.
try:  # pragma: no cover - trivial compatibility shim
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except Exception:  # pragma: no cover - fallback when pkg_resources is absent
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

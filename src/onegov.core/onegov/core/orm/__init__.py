from onegov.core.orm.session_manager import SessionManager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import TranslationHybrid

#: The base for all OneGov Core ORM Models
Base = declarative_base()

#: A translation hybrid integrated with OneGov Core. See also:
#: http://sqlalchemy-utils.readthedocs.org/en/latest/internationalization.html
translation_hybrid = TranslationHybrid(
    current_locale=lambda obj: obj.session_manager.current_locale,
    default_locale=lambda obj: obj.session_manager.default_locale,
)

__all__ = ['Base', 'SessionManager', 'translation_hybrid']

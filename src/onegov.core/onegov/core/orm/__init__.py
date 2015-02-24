from onegov.core.orm.session_manager import SessionManager
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

__all__ = ['Base', 'SessionManager']

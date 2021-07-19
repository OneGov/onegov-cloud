from onegov.core.orm import ModelBase
from onegov.core.orm import SessionManager
from onegov.core.orm.mixins import ContentMixin
from onegov.editorjs.models import editorjs_content, EditorJsDBField
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declarative_base


def test_editor_js(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Page(Base, ContentMixin):
        __tablename__ = 'pages'
        id = Column(Integer, primary_key=True)
        text = editorjs_content()

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    session = mgr.session()
    session.add(Page())
    session.flush()

    page = session.query(Page).one()
    assert page.text.blocks == []
    assert page.text.version is None
    assert page.text.time is None

    page = session.query(Page).one()
    page.text = EditorJsDBField(blocks=[
        {
            "type": "paragraph",
            "data": {
                "text": "Hey zäme."
            }
        }
    ])
    assert page.text.blocks[0]['type'] == 'paragraph'
    assert page.text.blocks[0]['data']['text'] == 'Hey zäme.'
    session.flush()
    mgr.dispose()

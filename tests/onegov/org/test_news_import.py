from __future__ import annotations

import json

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml

from click.testing import CliRunner
from transaction import commit

from onegov.org.cli import cli
from onegov.org.models.page import Page
from onegov.page.collection import PageCollection

if TYPE_CHECKING:
    from onegov.core.orm import SessionManager


def text(value: str) -> dict[str, Any]:
    return {'type': 'Text', 'text': value}


def paragraph(*children: dict[str, Any]) -> dict[str, Any]:
    return {'type': 'Paragraph', 'children': list(children)}


def test_import_news_cli(
    cfg_path: str,
    session_manager: SessionManager,
    tmp_path: Path,
) -> None:
    # configure the instance as an OrgApp
    config_path = Path(cfg_path)
    config = yaml.safe_load(config_path.read_text())
    application = config['applications'][0]
    application['application'] = 'onegov.org.OrgApp'
    application['configuration'][
        'depot_backend'
    ] = 'depot.io.memory.MemoryFileStorage'
    application['configuration']['websockets'] = {
        'client_url': 'ws://localhost:8766',
        'manage_url': 'ws://localhost:8766',
        'manage_token': 'news-local-test-token',
    }
    application['configuration']['filestorage'] = 'fs.osfs.OSFS'
    application['configuration']['filestorage_options'] = {
        'root_path': str(tmp_path / 'storage'),
        'create': True,
    }
    config_path.write_text(yaml.safe_dump(config))

    # the scraper names news files '<id>.json' (no date prefix) and carries the
    # publication date only in the metadata -- the regression this guards is
    # import-news parsing the date from the filename and crashing on such names
    news_dir = tmp_path / 'news'
    news_dir.mkdir()
    for number, title, published in (
        ('2573620', 'First news', '2024-01-15T10:00:00'),
        ('2605471', 'Second news', '2024-02-20T08:30:00'),
    ):
        (news_dir / f'{number}.json').write_text(json.dumps({
            'metadata': {'title': title, 'published': published},
            'elements': [paragraph(text(f'Body of {title}'))],
        }))

    runner = CliRunner()
    base = ['--config', cfg_path, '--select', '/foo/bar']
    cmd = [*base, 'import-news', str(news_dir)]

    # a first run bootstraps the schema/tables; ensure a news parent exists
    runner.invoke(cli, cmd, catch_exceptions=False)
    session_manager.set_current_schema('foo-bar')
    session = session_manager.session()
    if not session.query(Page).filter(
        Page.type == 'news', Page.parent_id.is_(None)
    ).first():
        PageCollection(session).add_root('Aktuelles', type='news')
        commit()

    def news_articles() -> list[Page]:
        session_manager.set_current_schema('foo-bar')
        return session_manager.session().query(Page).filter(
            Page.type == 'news', Page.parent_id.isnot(None)
        ).order_by(Page.publication_start).all()

    # dry-run parses the <id>.json files (no crash) but writes nothing
    result = runner.invoke(cli, [*cmd, '--dry-run'], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert '2 news items imported' in result.output
    assert news_articles() == []

    # the real import creates the two news pages, dated from the metadata
    result = runner.invoke(cli, cmd, catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert '2 news items imported' in result.output
    articles = news_articles()
    assert [a.title for a in articles] == ['First news', 'Second news']
    assert articles[0].publication_start == datetime(
        2024, 1, 15, 10, 0, tzinfo=UTC)

    # re-running is idempotent (matched by title + publication date)
    result = runner.invoke(cli, cmd, catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert 'already exists' in result.output
    assert len(news_articles()) == 2

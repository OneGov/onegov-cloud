import yaml

from click.testing import CliRunner
from onegov.core.custom import json
from onegov.core.orm.audit import AuditEntry
from onegov.org.cli import cli
from onegov.org.models.page import Topic
from onegov.page import Page
from onegov.page.audit import page_tree_snapshot
from transaction import commit


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from onegov.core.orm import SessionManager


def test_restore_page_cli(
    cfg_path: str,
    session_manager: SessionManager,
    tmp_path: Path,
) -> None:
    with open(cfg_path) as config_file:
        config = yaml.safe_load(config_file)
    application = config['applications'][0]
    application['application'] = 'onegov.org.OrgApp'
    application['configuration']['enable_search'] = False
    application['configuration']['filestorage'] = 'fs.osfs.OSFS'
    application['configuration']['filestorage_options'] = {
        'root_path': str(tmp_path / 'storage'),
        'create': True,
    }
    application['configuration']['websockets'] = application['websockets']
    application['configuration'][
        'depot_backend'
    ] = 'depot.io.memory.MemoryFileStorage'
    with open(cfg_path, 'w') as config_file:
        yaml.safe_dump(config, config_file)
    session_manager.set_current_schema('foo-bar')
    session = session_manager.session()
    page = Topic(title='Original', name='original', meta={'access': 'private'})
    session.add(page)
    session.flush()
    page_id = page.id
    snapshot = json.loads(json.dumps(page_tree_snapshot(page)))
    path = tmp_path / 'snapshot.json'
    path.write_text(json.dumps(snapshot), encoding='utf-8')
    session.delete(page)
    commit()

    runner = CliRunner()
    args = [
        '--config',
        cfg_path,
        '--select',
        '/foo/bar',
        'restore-page',
        str(path),
    ]
    result = runner.invoke(cli, [*args, '--dry-run'], catch_exceptions=False)
    assert result.exit_code == 0
    assert 'No changes saved' in result.output
    assert session_manager.session().get(Page, page_id) is None
    assert session_manager.session().query(AuditEntry).count() == 0

    result = runner.invoke(cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    assert 'Restored 1 page(s)' in result.output
    restored = session_manager.session().get(Page, page_id)
    assert isinstance(restored, Topic)
    assert page_tree_snapshot(restored) == snapshot
    audit = session_manager.session().query(AuditEntry).one()
    assert audit.username == 'cli:restore-page'
    assert audit.operation == 'insert'

    snapshot['title'] = 'Must not persist'
    snapshot['file_ids'] = ['missing-file']
    path.write_text(json.dumps(snapshot), encoding='utf-8')
    result = runner.invoke(cli, args)
    assert result.exit_code != 0
    assert 'Missing files: missing-file' in result.output
    restored = session_manager.session().get(Page, page_id)
    assert restored is not None
    assert restored.title == 'Original'

    snapshot['file_ids'] = []
    snapshot['children'] = [
        {
            **snapshot,
            'id': page_id + 1,
            'parent_id': page_id,
            'name': 'invalid-child',
            'title': None,
            'children': [],
        }
    ]
    path.write_text(json.dumps(snapshot), encoding='utf-8')
    result = runner.invoke(cli, args)
    assert result.exit_code != 0
    restored = session_manager.session().get(Page, page_id)
    assert restored is not None
    assert restored.title == 'Original'
    assert restored.children == []
    assert session_manager.session().query(AuditEntry).count() == 1

    snapshot['children'] = []
    snapshot['file_ids'] = ['missing-file']
    snapshot['title'] = 'Updated from snapshot'
    path.write_text(json.dumps(snapshot), encoding='utf-8')
    result = runner.invoke(
        cli,
        [*args, '--skip-missing-files', '--dry-run'],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    restored = session_manager.session().get(Page, page_id)
    assert restored is not None
    assert restored.title == 'Original'
    assert session_manager.session().query(AuditEntry).count() == 1

    result = runner.invoke(
        cli,
        [*args, '--skip-missing-files'],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert 'Skipping missing files: missing-file' in result.output
    restored = session_manager.session().get(Page, page_id)
    assert restored is not None
    assert restored.title == 'Updated from snapshot'
    assert restored.files == []
    update = (
        session_manager.session()
        .query(AuditEntry)
        .filter_by(
            operation='update',
        )
        .one()
    )
    assert update.username == 'cli:restore-page'
    assert update.previous_snapshot['title'] == 'Original'
    assert update.snapshot['title'] == 'Updated from snapshot'

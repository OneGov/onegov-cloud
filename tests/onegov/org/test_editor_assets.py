from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import re
from typing import Any
from unittest.mock import Mock

import morepath
import pytest

from onegov.agency import AgencyApp
from onegov.agency.layout import AgencyLayout
from onegov.org import OrgApp
from onegov.org.layout import Layout
from onegov.town6 import TownApp


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VERSION = re.compile(
    r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?'
)


@pytest.mark.parametrize('base_app', (OrgApp, TownApp, AgencyApp))
def test_blocknote_editor_assets_are_registered(
    base_app: type[OrgApp],
) -> None:
    app_class = type('EditorAssetTestApp', (base_app,), {})
    morepath.commit(app_class)

    registry = app_class().config.webasset_registry
    blocknote = registry.assets['blocknote']
    editor = registry.assets['editor']

    assert blocknote.assets == (
        'blocknote.bundle.min.js',
        'blocknote.bundle.min.css',
    )
    assert blocknote.filters == {'js': None, 'css': None}
    assert editor.assets == ('input_with_button.js', 'editor.js')
    assert 'redactor' not in registry.assets

    assert registry.assets['blocknote.bundle.min.js'].path.endswith(
        'onegov/org/assets/js/blocknote.bundle.min.js'
    )
    assert registry.assets['blocknote.bundle.min.css'].path.endswith(
        'onegov/org/assets/css/blocknote.bundle.min.css'
    )


@pytest.mark.parametrize(
    'include_editor',
    (Layout.include_editor, AgencyLayout.include_editor),
    ids=('org', 'agency'),
)
def test_layout_includes_blocknote_before_adapter(
    include_editor: Callable[[Any], None],
) -> None:
    request = Mock()
    layout = Mock(request=request)

    include_editor(layout)

    assert [call.args for call in request.include.call_args_list] == [
        ('blocknote',),
        ('editor',),
    ]


def test_blocknote_bundle_has_an_immutable_update_boundary() -> None:
    source = PROJECT_ROOT / 'src/onegov/org/assets/src/blocknote'
    bundle = (
        PROJECT_ROOT
        / 'src/onegov/org/assets/js/blocknote.bundle.min.js'
    )
    stylesheet = (
        PROJECT_ROOT
        / 'src/onegov/org/assets/css/blocknote.bundle.min.css'
    )
    license_file = bundle.with_name(bundle.name + '.LEGAL.txt')
    package = json.loads((source / 'package.json').read_text())
    lock = json.loads((source / 'package-lock.json').read_text())
    javascript = bundle.read_text()
    licenses = license_file.read_text()

    dependencies = {
        **package['dependencies'],
        **package['devDependencies'],
    }
    locked_root = {
        **lock['packages']['']['dependencies'],
        **lock['packages']['']['devDependencies'],
    }

    for name, version in dependencies.items():
        assert VERSION.fullmatch(version)
        assert locked_root[name] == version
        locked = lock['packages'][f'node_modules/{name}']
        assert locked['version'] == version
        assert locked['integrity'].startswith('sha512-')

    blocknote_version = dependencies['@blocknote/core']
    blocknote_versions = {
        version for name, version in dependencies.items()
        if name.startswith('@blocknote/')
    }
    assert blocknote_versions == {blocknote_version}

    assert package['engines']['node'] == '>=20.19.0'
    assert package['scripts']['check'] == 'node build.mjs --check'
    assert package['scripts']['verify:clean'].startswith('npm ci &&')
    assert javascript.startswith(
        f'/*! BlockNote {blocknote_version} bundled for OneGov; '
        'MPL-2.0/GPL-3.0'
    )
    assert re.search(r'\b(?:Function|eval)\s*\(', javascript) is None
    assert stylesheet.stat().st_size > 100_000

    assert licenses.startswith('GENERATED FILE - DO NOT EDIT\n\n')
    assert (
        f'@blocknote/core@{blocknote_version} (MPL-2.0)' in licenses
    )
    assert (
        f'@blocknote/xl-ai@{blocknote_version} '
        '(GPL-3.0 OR PROPRIETARY)' in licenses
    )
    assert 'Mozilla Public License Version 2.0' in licenses
    assert f'react@{dependencies["react"]} (MIT)' in licenses
    assert license_file.stat().st_size > 100_000

    assert {
        path.relative_to(source).as_posix()
        for path in source.rglob('*')
        if path.is_file()
        and 'node_modules' not in path.relative_to(source).parts
    } == {
        '.gitignore',
        'README.md',
        'blocknote-editor.css',
        'blocknote-editor.jsx',
        'build.mjs',
        'package-lock.json',
        'package.json',
    }


def test_resource_picker_adapters_stay_in_sync() -> None:
    org_picker = (
        PROJECT_ROOT / 'src/onegov/org/assets/js/input_with_button.js'
    )
    town_picker = (
        PROJECT_ROOT / 'src/onegov/town6/assets/js/input_with_button.js'
    )

    assert town_picker.read_bytes() == org_picker.read_bytes()

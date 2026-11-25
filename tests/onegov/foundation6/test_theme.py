from __future__ import annotations

from onegov.foundation6.theme import Theme


def test_theme_basic_properties() -> None:
    theme = Theme()
    assert theme.name == 'zurb.foundation'
    assert theme.default_options == {}
    assert theme.pre_imports == []
    assert theme.post_imports == []
    assert theme.extra_search_paths == []
    assert theme.foundation_styles == ('global-styles', 'forms', 'typography')
    assert 'button' in theme.foundation_components
    assert '@include' in theme.foundation_helpers


def test_theme_config_vars() -> None:
    joined = '\n'.join(Theme().foundation_config_vars)
    assert '$flex: false' in joined
    assert '$prototype: false' in joined


def test_theme_paths() -> None:
    theme = Theme()
    assert theme.foundation_path.endswith('foundation/foundation/scss')
    assert theme.vendor_path.endswith('foundation/vendor')


def test_theme_includes() -> None:
    includes = list(Theme().includes)
    assert any('foundation-button' in i for i in includes)
    assert any('foundation-global-styles' in i for i in includes)
    assert any('foundation-typography' in i for i in includes)


def test_theme_motion_ui_disabled_by_default() -> None:
    assert Theme().foundation_motion_ui == []

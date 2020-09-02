from onegov.translator_directory.layout import TranslatorLayout


def test_translator_layout(session):
    assert TranslatorLayout.format_languages(None) == ''
    assert TranslatorLayout.format_drive_distance(None) == ''
    assert TranslatorLayout.format_drive_distance(5) == '5 km'

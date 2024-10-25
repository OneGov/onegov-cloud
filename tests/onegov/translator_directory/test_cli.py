from click.testing import CliRunner
from transaction import commit

from onegov.translator_directory.cli import cli, LANGUAGES
from onegov.translator_directory.models.language import Language


def test_create_languages(cfg_path, session_manager, translator_app):
    runner = CliRunner()
    session_manager.ensure_schema_exists('translator_directory')
    session_manager.set_current_schema('translator_directory-deadbeef')

    def languages():
        return get_session().query(Language)

    def by_name(name):
        return languages().filter(Language.name == name).one()

    def get_session():
        return session_manager.session()

    # recreate from scratch
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'create-languages'
    ])
    assert result.exit_code == 0
    assert f'Inserted {len(LANGUAGES)} languages' in result.output
    assert languages().count() == len(LANGUAGES)

    # add lorem language manually
    get_session().add(Language(name='Lorem'))
    commit()
    assert languages().count() == len(LANGUAGES) + 1

    # manually add language
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'create-languages'
    ])
    assert result.exit_code == 0
    assert 'Inserted 0 languages' in result.output
    assert 'Language \'Lorem\' is unknown' in result.output
    assert languages().count() == len(LANGUAGES) + 1

    # manually rename language
    languages().first().name += ' RENAMED'
    commit()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'create-languages'
    ])
    assert result.exit_code == 0
    assert 'Inserted 1 languages' in result.output
    assert 'Language \'Afrikaans RENAMED\' is unknown' in result.output
    assert 'Language \'Lorem\' is unknown' in result.output
    assert languages().count() == len(LANGUAGES) + 2

    # manually delete languages, then recreate
    get_session().delete(by_name('Afrikaans RENAMED'))
    get_session().delete(by_name('Lorem'))
    get_session().delete(languages().first())
    get_session().delete(languages().first())
    commit()
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'create-languages'
    ])
    assert result.exit_code == 0
    assert 'Inserted 2 languages' in result.output
    assert 'unknown' not in result.output
    assert languages().count() == len(LANGUAGES)

    # execute dry run
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'create-languages',
        '--dry-run'
    ])
    assert result.exit_code == 0
    assert 'Inserted 0 languages' in result.output
    assert 'unknown' not in result.output
    assert 'Aborting transaction' in result.output
    assert languages().count() == len(LANGUAGES)


def test_delete_languages(cfg_path, session_manager, translator_app):
    runner = CliRunner()
    session_manager.ensure_schema_exists('translator_directory')
    session_manager.set_current_schema('translator_directory-deadbeef')

    def languages():
        return get_session().query(Language)

    def by_name(name):
        return languages().filter(Language.name == name).one()

    def get_session():
        return session_manager.session()

    # add some languages
    for name in ('Lorem', 'Ipsum', 'Dolor'):
        get_session().add(Language(name=name))
    commit()
    assert languages().count() == 3

    # dry run
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'force-delete-languages',
        '--dry-run',
    ], input='y')
    assert result.exit_code == 0
    assert 'Aborting transaction' in result.output
    assert languages().count() == 3

    # delete all languages, missing confirmation
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'force-delete-languages',
    ], input='panic!')
    assert result.exit_code == 0
    assert 'Aborting transaction' in result.output
    assert languages().count() == 3

    # finally delete all languages
    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/deadbeef',
        'force-delete-languages',
    ], input='y')
    assert result.exit_code == 0
    assert languages().count() == 0

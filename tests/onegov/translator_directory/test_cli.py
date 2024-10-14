from click.testing import CliRunner
from transaction import commit

from onegov.translator_directory.cli import cli, LANGUAGES
from onegov.translator_directory.models.language import Language
from onegov.translator_directory.models.translator import Translator


def test_migrate_nationalities(cfg_path, session_manager, translator_app):
    runner = CliRunner()
    session_manager.ensure_schema_exists('translator_directory')
    session_manager.set_current_schema('translator_directory-bar')

    def translators():
        return get_session().query(Translator)

    def by_last_name(last_name):
        return translators().filter(Translator.last_name == last_name).one()

    def get_session():
        return session_manager.session()

    # Add some translators
    for first, last, nationality in (
        ('Hans', 'Moleman', 'CH'),
        ('Dieter', 'Brüggemann', 'Schweiz Deutschland'),
        ('Meri', 'Jackson', 'Grossbritannien, Österreich'),
        ('Marta', 'Schmidt', 'Oesterreich'),
        ('X', 'Y', 'Tibet'),
        ('Xia', 'Yi', 'China'),
        ('Mika', 'Petkovic', 'Bosnien und Herzegowina'),
        ('Pietr', 'Petrov', 'Slowakische Republik'),
        ('Myrko', 'Tomic', 'Tschechische Republik'),
        ('Emrah', 'Üzgül', 'Türkei'),
        ('F', 'SMI', 'Schweiz Mexiko, Iran'),
        ('R', 'SBuH', 'Schweiz; Bosnien und Herzegowina'),
        ('Ruth', 'Letkova', 'Lettland/Italien'),
        ('Francois', 'Paris', 'Frankreich; Schweiz'),
        ('Frieda', 'Hausmann', 'Schweiz\nMonaco'),
        ('Mila', 'Matkovatsch', 'CH, PL, RU')
    ):
        get_session().add(
            Translator(
                first_name=first,
                last_name=last,
                nationality=nationality,
            )
        )
    commit()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/bar',
        'migrate-nationalities'
    ])
    assert result.exit_code == 0
    assert 'Migration successful for 16 translators' in result.output

    assert translators().count() == 16
    expected_nationalities = {
        'Moleman': ['CH'],
        'Brüggemann': ['CH', 'DE'],
        'Jackson': ['GB', 'AT'],
        'Schmidt': ['AT'],
        'Y': ['CN'],
        'Yi': ['CN'],
        'Petkovic': ['BA'],
        'Petrov': ['SK'],
        'Tomic': ['CZ'],
        'Üzgül': ['TR'],
        'SMI': ['CH', 'MX', 'IR'],
        'SBuH': ['CH', 'BA'],
        'Letkova': ['LV', 'IT'],
        'Paris': ['FR', 'CH'],
        'Hausmann': ['CH', 'MC'],
        'Matkovatsch': ['CH', 'PL', 'RU'],
    }
    assert all(set(by_last_name(last_name).nationalities) == set(expected)
               for last_name, expected in expected_nationalities.items())

    # unknown nationalities
    get_session().add(
        Translator(
            first_name='Felippe',
            last_name='Santos',
            nationality='Sppanien',
        )
    )
    commit()

    result = runner.invoke(cli, [
        '--config', cfg_path,
        '--select', '/translator_directory/bar',
        'migrate-nationalities'
    ])
    assert result.exit_code == 0
    assert 'Unknown: \'Sppanien\'' in result.output
    assert 'Migration failed for 1 translator(s) of 17' in result.output


def test_create_lanugages(cfg_path, session_manager, translator_app):
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

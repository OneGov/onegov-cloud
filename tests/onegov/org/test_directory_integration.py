import transaction

from onegov.directory import DirectoryCollection, DirectoryConfiguration, \
    DirectoryZipArchive


def test_directory_roundtrip(session, temporary_path):
    export_fmt = 'json'
    directories = DirectoryCollection(session)
    dir_structure = "Name *= ___\nContact (for infos) = ___"
    events = directories.add(
        title="Events",
        lead="The town's events",
        structure=dir_structure,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    events.add(values=dict(name="Dance", contact_for_infos_='John'))
    transaction.commit()

    events = directories.by_name('events')

    archive = DirectoryZipArchive(temporary_path / 'archive.zip', export_fmt)
    archive.write(events)

    archive = DirectoryZipArchive.from_buffer(
        (temporary_path / 'archive.zip').open('rb'))

    directory = archive.read()

    assert directory.title == "Events"
    assert directory.lead == "The town's events"
    assert directory.structure == dir_structure
    assert directory.fields[1].id == 'contact_for_infos_'
    assert len(directory.entries) == 1

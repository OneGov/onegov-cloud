from onegov.directory import DirectoryCollection


def test_directory_title_and_order(session):
    doctors = DirectoryCollection(session).add(
        title='Doctors',
        structure='',
        configuration=''
    )

    assert doctors.name == 'doctors'
    assert doctors.order == 'doctors'

    doctors.title = "General Practicioners"
    session.flush()

    assert doctors.name == 'doctors'
    assert doctors.order == 'general-practicioners'

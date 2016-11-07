import os
import transaction

from onegov.core.datamanager import FileDataManager


def test_file_data_manager_commit(temporary_directory):

    data = 'data'.encode('utf-8')
    path = '{}/a.txt'.format(temporary_directory)
    FileDataManager.write_file(data, path)
    manager = transaction.get()._resources[0]

    assert manager.data == data
    assert manager.path == path
    assert not os.path.exists(path)

    transaction.commit()
    assert os.path.exists(path)
    with open(path) as file:
        assert file.read() == 'data'

    os.remove(path)


def test_file_data_manager_abort(temporary_directory):

    data = 'data'.encode('utf-8')
    path = '{}/b.txt'.format(temporary_directory)
    FileDataManager.write_file(data, path)
    manager = transaction.get()._resources[0]

    assert manager.data == data
    assert manager.path == path
    assert not os.path.exists(path)

    transaction.abort()
    assert not os.path.exists(path)

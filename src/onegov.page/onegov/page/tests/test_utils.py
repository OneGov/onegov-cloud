from onegov.page import utils


def test_increment_name():
    assert utils.increment_name('test') == 'test-1'
    assert utils.increment_name('test-2') == 'test-3'
    assert utils.increment_name('test2') == 'test2-1'
    assert utils.increment_name('test-1-1') == 'test-1-2'

from onegov.core import utils


def test_normalize_for_url():
    assert utils.normalize_for_url('asdf') == 'asdf'
    assert utils.normalize_for_url('Asdf') == 'asdf'
    assert utils.normalize_for_url('A S d f') == 'a-s-d-f'
    assert utils.normalize_for_url('far  away') == 'far-away'
    assert utils.normalize_for_url('währung') == 'wahrung'


def test_lchop():
    assert utils.lchop('foobar', 'foo') == 'bar'
    assert utils.lchop('foobar', 'bar') == 'foobar'


def test_rchop():
    assert utils.rchop('foobar', 'foo') == 'foobar'
    assert utils.rchop('foobar', 'bar') == 'foo'

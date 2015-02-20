from onegov.core import utils


def test_lchop():
    assert utils.lchop('foobar', 'foo') == 'bar'
    assert utils.lchop('foobar', 'bar') == 'foobar'


def test_rchop():
    assert utils.rchop('foobar', 'foo') == 'foobar'
    assert utils.rchop('foobar', 'bar') == 'foo'

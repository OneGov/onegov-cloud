# -*- coding: utf-8 -*-

from onegov.core import utils


def test_normalize_for_url():
    assert utils.normalize_for_url(u'asdf') == 'asdf'
    assert utils.normalize_for_url(u'Asdf') == 'asdf'
    assert utils.normalize_for_url(u'A S d f') == 'a-s-d-f'
    assert utils.normalize_for_url(u'far  away') == 'far-away'
    assert utils.normalize_for_url(u'währung') == 'wahrung'


def test_lchop():
    assert utils.lchop('foobar', 'foo') == 'bar'
    assert utils.lchop('foobar', 'bar') == 'foobar'


def test_rchop():
    assert utils.rchop('foobar', 'foo') == 'foobar'
    assert utils.rchop('foobar', 'bar') == 'foo'

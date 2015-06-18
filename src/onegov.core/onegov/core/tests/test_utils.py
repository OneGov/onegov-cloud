# -*- coding: utf-8 -*-

import onegov.core
import os.path

from onegov.core import utils


def test_normalize_for_url():
    assert utils.normalize_for_url(u'asdf') == 'asdf'
    assert utils.normalize_for_url(u'Asdf') == 'asdf'
    assert utils.normalize_for_url(u'A S d f') == 'a-s-d-f'
    assert utils.normalize_for_url(u'far  away') == 'far-away'
    assert utils.normalize_for_url(u'währung') == 'wahrung'
    assert utils.normalize_for_url(u'one/two') == 'one-two'
    assert utils.normalize_for_url('far / away') == 'far-away'
    assert utils.normalize_for_url('far <away>') == 'far-away'
    assert utils.normalize_for_url('far (away)') == 'far-away'


def test_lchop():
    assert utils.lchop('foobar', 'foo') == 'bar'
    assert utils.lchop('foobar', 'bar') == 'foobar'


def test_rchop():
    assert utils.rchop('foobar', 'foo') == 'foobar'
    assert utils.rchop('foobar', 'bar') == 'foo'


def test_touch(temporary_directory):
    path = os.path.join(temporary_directory, 'test.txt')

    assert not os.path.isfile(path)

    utils.touch(path)

    assert os.path.isfile(path)

    with open(path, 'w') as f:
        f.write('asdf')

    utils.touch(path)

    with open(path, 'r') as f:
        assert f.read() == 'asdf'


def test_module_path():
    path = utils.module_path('onegov.core', 'utils.py')
    assert path == utils.module_path(onegov.core, 'utils.py')
    assert os.path.isfile(path)

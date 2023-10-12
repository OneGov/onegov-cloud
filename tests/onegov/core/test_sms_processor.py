import json
import os

from onegov.core.framework import Framework
from onegov.core.sms_processor import SmsQueueProcessor
from onegov.core.sms_processor import get_sms_queue_processor
from pytest import raises
from unittest.mock import Mock


def test_sms_queue_processor(temporary_directory):
    sms_path = os.path.join(
        temporary_directory, 'sms', 'onegov_town6-meggen'
    )
    os.makedirs(sms_path)

    qp = SmsQueueProcessor(sms_path, 'username', 'password')
    qp.send = Mock(return_value=None)

    def create(name, receivers, content='Fancy new results!'):
        with open(os.path.join(sms_path, name), 'w') as f:
            f.write(json.dumps({
                'receivers': receivers, 'content': content
            }))

    valid = [
        ['one', ['+41791112233'], 'Fancy new results'],
        ['batch', ['+41794445566', '+41794445577'], 'Fancy new results'],
        ['0.000000', ['+41791112233'], 'Fancy new results'],
        ['0.1.054981', ['+41794445566'], 'Fancy new results'],
        ['0.1.aeerwe', ['+41797778899'], 'Fancy new results'],
        ['0.89791.98766', ['+41791112233'], 'Fancy new results'],
        ['0.1.2.3.4.-.334', ['+41794445566'], 'Fancy new results'],
        ['wo03.03002.', ['+41797778899'], 'Fancy new results'],
        ['one_invalid', ['+41797778899', 'invalid'], 'Fancy new results'],
    ]
    invalid = [
        ['missing_content', ['+41797779999'], ''],
        ['no_recipients', [], 'Fancy new results'],
        ['missing_list', '+41797779999', 'Fancy new results'],
        ['all_invalid', ['+41abcdef'], 'Fancy new results'],
    ]
    ignored = [
        ['.sending-0', ['+41791119999'], 'Fancy new results'],
        ['.rejected-0', ['+41791119999'], 'Fancy new results'],
        ['.qq89988e7e', ['+41791119999'], 'Fancy new results'],
    ]
    for name, receivers, content in valid + invalid + ignored:
        create(name, receivers, content)

    qp.send_messages()

    for name, receivers, content in valid + invalid:
        assert not os.path.exists(os.path.join(sms_path, name))
    for name, receivers, content in invalid:
        assert os.path.exists(os.path.join(sms_path, '.rejected-' + name))
    for name, receivers, content in ignored:
        assert os.path.exists(os.path.join(sms_path, name))

    assert qp.send.called

    assert sorted([t[0][0] for t in qp.send.call_args_list]) == [
        ('+41791112233',),
        ('+41791112233',),
        ('+41791112233',),
        ('+41794445566',),
        ('+41794445566',),
        ('+41794445566', '+41794445577'),
        ('+41797778899',),
        ('+41797778899',),
        ('+41797778899',),
    ]


def test_sms_queue_processor_failed(temporary_directory):
    sms_path = os.path.join(
        temporary_directory, 'sms', 'onegov_town6-meggen'
    )
    os.makedirs(sms_path)

    qp = SmsQueueProcessor(sms_path, 'username', 'password')
    qp.send = Mock(return_value={'StatusCode': '0'})

    filename = '0.1.0.0'
    with open(os.path.join(sms_path, filename), 'w') as f:
        f.write(json.dumps({
            'receivers': ['+41791112233'],
            'content': 'Fancy new results'
        }))

    qp.send_messages()
    assert qp.send.called
    assert not os.path.exists(os.path.join(sms_path, filename))
    assert os.path.exists(os.path.join(sms_path, '.failed-' + filename))


def test_sms_queue_processor_send():
    processor = SmsQueueProcessor('path', 'username', 'password')
    processor.send_request = Mock()

    processor.send_request.return_value = (200, '{}')
    assert processor.send(['1234'], 'content') == {}

    processor.send_request.return_value = (
        200, '{"StatusInfo": "ERROR", "StatusCode": "0"}')
    assert processor.send(['1234'], 'content') == {
        'StatusInfo': 'ERROR',
        'StatusCode': '0'
    }

    processor.send_request.return_value = (500, 'Error')
    with raises(RuntimeError):
        processor.send(['1234'], 'content')

    processor.send_request.return_value = (
        200, '{"StatusInfo": "OK", "StatusCode": "1"}')
    assert processor.send(['1234'], 'content') == None


def test_get_sms_queue_processor(tmpdir):
    smsdir = tmpdir.mkdir('sms')
    schemadir = str(smsdir.join('test'))
    app = Framework()
    app.schema = 'test'
    app.application_id = 'test'
    app.sms_directory = None
    app.sms_user = None
    app.sms_password = None
    app.sms_originator = None
    app.sms = {}
    assert get_sms_queue_processor(app) is None

    app.sms_directory = smsdir
    assert get_sms_queue_processor(app) is None
    assert get_sms_queue_processor(app, missing_path_ok=True) is None

    app.sms_user = 'shared'
    app.sms_password = 'sharedpw'

    assert get_sms_queue_processor(app) is None
    qp = get_sms_queue_processor(app, missing_path_ok=True)
    assert qp.path == os.path.abspath(schemadir)
    assert qp.username == 'shared'
    assert qp.password == 'sharedpw'
    assert qp.originator == 'OneGov'

    app.sms_originator = 'shared'
    app.sms['test'] = {
        'user': 'test',
        'password': 'testpw',
        'originator': None
    }
    qp = get_sms_queue_processor(app, missing_path_ok=True)
    assert qp.path == os.path.abspath(schemadir)
    assert qp.username == 'test'
    assert qp.password == 'testpw'
    assert qp.originator == 'shared'

    app.sms['test']['originator'] = 'test'
    smsdir.mkdir('test')
    qp = get_sms_queue_processor(app)
    assert qp.path == os.path.abspath(schemadir)
    assert qp.username == 'test'
    assert qp.password == 'testpw'
    assert qp.originator == 'test'

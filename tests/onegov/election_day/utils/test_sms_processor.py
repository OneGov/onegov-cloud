import os

from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from pytest import raises
from unittest.mock import Mock


def test_sms_queue_processor(election_day_app, temporary_directory):
    sms_path = os.path.join(
        temporary_directory, 'sms', election_day_app.schema
    )
    os.makedirs(sms_path)

    qp = SmsQueueProcessor(sms_path, 'username', 'password')
    qp.send = Mock()

    def create(name, content='Fancy new results!'):
        with open(os.path.join(sms_path, name), 'w') as f:
            f.write(content)

    valid = [
        ['+41791112233', 'Fancy new results'],
        ['+41794445566', 'Fancy new results'],
        ['+41791112233.000000', 'Fancy new results'],
        ['+41794445566.054981', 'Fancy new results'],
        ['+41797778899.aeerwe', 'Fancy new results'],
        ['+41791112233.89791.98766', 'Fancy new results'],
        ['+41794445566.1.2.3.4.-.334', 'Fancy new results'],
        ['+41797778899.wo03.03002.', 'Fancy new results'],
    ]
    invalid = [
        ['+41797778899', ''],
        ['+41abcdef', 'Fancy new results'],
    ]
    ignored = [
        ['0041794445566', 'Fancy new results'],
        ['0794445566', 'Fancy new results'],
        ['qq89988e7e', 'Fancy new results'],
    ]
    for name, content in valid + invalid + ignored:
        create(name, content)

    qp.send_messages()

    for name, content in valid:
        assert not os.path.exists(os.path.join(sms_path, name))
    for name, content in invalid:
        assert os.path.exists(os.path.join(sms_path, '.rejected-' + name))
    for name, content in ignored:
        assert os.path.exists(os.path.join(sms_path, name))

    assert qp.send.called

    sorted([t[0][0] for t in qp.send.call_args_list]) == [
        '+41791112233',
        '+41791112233',
        '+41791112233',
        '+41794445566',
        '+41794445566',
        '+41794445566',
        '+41797778899',
        '+41797778899',
    ]


def test_sms_queue_processor_send():
    processor = SmsQueueProcessor('path', 'username', 'password')
    processor.send_request = Mock()

    processor.send_request.return_value = (200, '{}')
    with raises(RuntimeError):
        processor.send('1234', 'content')

    processor.send_request.return_value = (
        200, '{"StatusInfo": "ERROR", "StatusCode": "0"}')
    with raises(RuntimeError):
        processor.send('1234', 'content')

    processor.send_request.return_value = (500, 'Error')
    with raises(RuntimeError):
        processor.send('1234', 'content')

    processor.send_request.return_value = (
        200, '{"StatusInfo": "OK", "StatusCode": "1"}')
    processor.send('1234', 'content')

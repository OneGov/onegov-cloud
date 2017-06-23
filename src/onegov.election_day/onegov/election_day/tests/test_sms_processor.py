import os

from onegov.election_day.utils.sms_processor import SmsQueueProcessor
from pytest import raises
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch


def test_sms_queue_processor(election_day_app, temporary_directory):
    sms_path = os.path.join(
        temporary_directory, 'sms', election_day_app.schema
    )
    os.makedirs(sms_path)

    qp = SmsQueueProcessor(sms_path, 'username', 'password')
    qp._send = Mock()

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

    assert qp._send.called

    sorted([t[0][0] for t in qp._send.call_args_list]) == [
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

    with patch(
        'onegov.election_day.utils.sms_processor.post',
        return_value=MagicMock(json=lambda: {})
    ) as post:
        with raises(Exception):
            processor._send('1234', 'content')
        assert post.called

    with patch(
        'onegov.election_day.utils.sms_processor.post',
        return_value=MagicMock(json=lambda: {
            'StatusInfo': 'ERROR',
            'StatusCode': '0'
        })
    ) as post:
        with raises(Exception):
            processor._send('1234', 'content')
        assert post.called

    with patch(
        'onegov.election_day.utils.sms_processor.post',
        return_value=MagicMock(json=lambda: {
            'StatusInfo': 'OK',
            'StatusCode': '1'
        })
    ) as post:
        processor._send('1234', 'content')
        assert post.called

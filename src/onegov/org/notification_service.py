from __future__ import annotations

from firebase_admin import messaging  # type:ignore[import-untyped]
from firebase_admin.exceptions import (  # type:ignore[import-untyped]
    FirebaseError
)
import firebase_admin
from firebase_admin import credentials as firebase_credentials

import json
import logging
from abc import ABC, abstractmethod
from typing import Any


logger = logging.getLogger(__name__)


class NotificationService(ABC):
    """It can't hurt to abstract this Firebase notification away.
    First and foremost, this should allow for testing without
    mocking the wohle house"""

    @abstractmethod
    def send_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Send a notification to a specific topic.

        Args:
            topic: The topic to send to
            title: Notification title
            body: Notification body
            data: Additional data to include

        Returns:
            str: Message ID or response
        """


class FirebaseNotificationService(NotificationService):
    """Firebase implementation of the notification service."""

    def __init__(self, credentials_json: str):
        """Initialize with Firebase credentials.

        Args:
            credentials_json: JSON string containing Firebase
                credentials
        """
        self.credentials_dict = json.loads(credentials_json)
        self._firebase_app = None

    def _get_firebase_app(self) -> Any:
        """Get or initialize the Firebase app instance.

        Returns:
            The Firebase app instance.
        """
        if self._firebase_app is None:

            try:
                # Try to get existing app
                self._firebase_app = firebase_admin.get_app()
                logger.debug('Using existing Firebase app.')
            except ValueError:
                # Initialize new app with credentials from dict
                cred = firebase_credentials.Certificate(
                    self.credentials_dict
                )
                self._firebase_app = firebase_admin.initialize_app(cred)
                logger.debug('Initialized new Firebase app.')

        return self._firebase_app

    def send_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Send notification via Firebase.

        Args:
            topic: Topic to send the notification to.
            title: The notification title.
            body: The notification body text.
            data: Optional additional data to include.

        Returns:
            The message ID from Firebase.
        """

        # Create the notification message
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            topic=topic,
        )

        # Send the message
        try:
            response = messaging.send(message, app=self._get_firebase_app())
            log_msg = f"Successfully sent notification to topic '{topic}'."
            log_msg += f' Response: {response}'
            logger.info(log_msg)
            return response
        except FirebaseError:
            log_msg = f"Firebase Messaging Error sending to topic '{topic}':"
            logger.exception(log_msg)
            raise  # Re-raise Firebase errors
        except Exception:
            log_msg = f"Unexpected error sending to topic '{topic}':"
            logger.exception(log_msg)
            raise  # Re-raise unexpected exceptions


class TestNotificationService(NotificationService):
    """Test implementation that records calls."""

    sent_messages: list[dict[str, str | dict[str, str]]]

    def __init__(self) -> None:
        self.sent_messages = []

    def send_notification(
        self,
        topic: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Record the notification without sending it."""
        message_id = f'test-message-{len(self.sent_messages)}'

        self.sent_messages.append(
            {
                'topic': topic,
                'title': title,
                'body': body,
                'data': data or {},
                'message_id': message_id,
            }
        )
        log_msg = 'Test Notification Service recorded message: '
        log_msg += f'{self.sent_messages[-1]}'
        logger.debug(log_msg)
        return message_id


# Global registry for testing
_TEST_NOTIFICATION_SERVICE: NotificationService | None = None


def get_notification_service(
    credentials_json: str | None = None,
) -> NotificationService:
    """
    Get the appropriate notification service.

    In tests, returns the test service if one has been registered.
    In production, returns a Firebase notification service.

    Args:
        credentials_json: Firebase credentials JSON for production use

    Returns:
        NotificationService: The notification service implementation
    """
    global _TEST_NOTIFICATION_SERVICE

    if _TEST_NOTIFICATION_SERVICE is not None:
        return _TEST_NOTIFICATION_SERVICE

    if credentials_json is None:
        raise ValueError('Firebase credentials required but not provided')

    return FirebaseNotificationService(credentials_json)


def set_test_notification_service(
    service: NotificationService | None = None,
) -> None:
    """
    Set a test notification service for testing purposes.

    Args:
        service: The test service to use, or None to clear
    """
    global _TEST_NOTIFICATION_SERVICE
    _TEST_NOTIFICATION_SERVICE = service

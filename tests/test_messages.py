from typing import Dict, Type

import footron_protocol as protocol
import pytest

test_application_message_body = {"number": 5, "object": {"nested": True}}
test_version = 1

serialized_messages = {
    "application app": (
        protocol.ApplicationAppMessage,
        {
            "type": protocol.MessageType.APPLICATION_APP,
            "version": test_version,
            "client": "test-client",
            "body": test_application_message_body,
        },
    ),
    "application client": (
        protocol.ApplicationClientMessage,
        {
            "type": protocol.MessageType.APPLICATION_CLIENT,
            "version": test_version,
            "app": "test-app",
            "body": test_application_message_body,
        },
    ),
    "application client request": (
        protocol.ApplicationClientMessage,
        {
            "type": protocol.MessageType.APPLICATION_CLIENT,
            "version": test_version,
            "client": "test-client",
            "body": test_application_message_body,
            "req": "test-req",
        },
    ),
    "heartbeat client": (
        protocol.HeartbeatClientMessage,
        {
            "type": protocol.MessageType.HEARTBEAT_CLIENT,
            "version": test_version,
            "clients": ["test-client1", "test-client2"],
            "up": True,
        },
    ),
    "heartbeat app": (
        protocol.HeartbeatAppMessage,
        {
            "type": protocol.MessageType.HEARTBEAT_APP,
            "version": test_version,
            "app": "test-app",
            "up": True,
        },
    ),
    "connect": (
        protocol.ConnectMessage,
        {
            "type": protocol.MessageType.CONNECT,
            "version": test_version,
            "client": "test-client",
        },
    ),
    "access": (
        protocol.AccessMessage,
        {
            "type": protocol.MessageType.ACCESS,
            "version": test_version,
            "client": "test-client",
            "accepted": False,
            "reason": "test reason",
        },
    ),
    "error": (
        protocol.ErrorMessage,
        {
            "type": protocol.MessageType.ERROR,
            "version": test_version,
            "error": "test error",
        },
    ),
    "display settings": (
        protocol.DisplaySettingsMessage,
        {
            "type": protocol.MessageType.DISPLAY_SETTINGS,
            "version": test_version,
            "settings": {
                "end_time": 6_28318530718,
                "lock": True
            },
        },
    ),
    "lifecycle": (
        protocol.LifecycleMessage,
        {
            "type": protocol.MessageType.LIFECYCLE,
            "version": test_version,
            "paused": False,
        },
    ),
}

serialized_message_params = [
    pytest.param(*v, id=k) for (k, v) in serialized_messages.items()
]


@pytest.mark.parametrize("msg_class, serialized_msg", serialized_message_params)
def test_deserialize_message(
    msg_class: Type[protocol.BaseMessage], serialized_msg: Dict
):
    """Check that message is correctly deserialized and serialized"""
    message = msg_class(**serialized_msg)
    assert serialized_msg == message.dict(exclude_none=True)


@pytest.mark.parametrize("msg_class, serialized_msg", serialized_message_params)
def test_identify_message_type(
    msg_class: Type[protocol.BaseMessage], serialized_msg: Dict
):
    """Check that class of serialized message is correctly identified"""
    assert(isinstance(protocol.deserialize(serialized_msg), msg_class))

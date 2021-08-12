from __future__ import annotations

from pydantic import BaseModel

import enum
from typing import Type, Optional, Any, Dict, List

from .types import JsonDict, Lock
from .errors import *

PROTOCOL_VERSION = 1
FIELD_MSG_TYPE = "type"


@enum.unique
class MessageType(str, enum.Enum):

    #
    # Heartbeat messages
    #

    #: App connection status update
    HEARTBEAT_APP = "ahb"
    #: Client connection status update
    HEARTBEAT_CLIENT = "chb"

    #
    # Authentication-level messages
    #

    #: Client connection request
    CONNECT = "con"
    #: App response to client connection request
    ACCESS = "acc"

    #
    # Application-level messages
    #

    #: Application-defined messages, including requests, from the client
    APPLICATION_CLIENT = "cap"
    #: Application-defined messages, including requests, from the app
    APPLICATION_APP = "app"
    #: Error in either direction; a simple message
    ERROR = "err"
    #: Request to change app runtime settings, handled by router
    DISPLAY_SETTINGS = "dse"
    #: Lifecycle updates (pause, resume)
    LIFECYCLE = "lcy"


class BaseMessage(BaseModel):
    type: MessageType
    version = PROTOCOL_VERSION


class AppClientIdentifiableMixin(BaseModel):
    """Fields for messages between an app and a client in either direction

    Note that the app to which messages sent by a client are bound is specified by
    the client connection request and the associated access response. The client has
    no other control over which app is the recipient of its messages.
    """

    client: Optional[str]
    app: Optional[str]


class BaseHeartbeatMessage(BaseMessage):
    up: bool


class HeartbeatAppMessage(BaseHeartbeatMessage, AppClientIdentifiableMixin):
    type = MessageType.HEARTBEAT_APP


class HeartbeatClientMessage(BaseHeartbeatMessage):
    clients: List[str]
    type = MessageType.HEARTBEAT_CLIENT


class ConnectMessage(BaseMessage, AppClientIdentifiableMixin):
    type: MessageType = MessageType.CONNECT


class AccessMessage(BaseMessage, AppClientIdentifiableMixin):
    accepted: bool
    reason: Optional[str] = None
    type = MessageType.ACCESS


class BaseApplicationMessage(BaseMessage):
    body: Any
    #: Request ID
    req: Optional[str] = None


class ApplicationClientMessage(BaseApplicationMessage, AppClientIdentifiableMixin):
    type = MessageType.APPLICATION_CLIENT


class ApplicationAppMessage(BaseApplicationMessage, AppClientIdentifiableMixin):
    type = MessageType.APPLICATION_APP


class ErrorMessage(BaseMessage):
    error: str
    type = MessageType.ERROR


class DisplaySettings(BaseModel):
    end_time: Optional[int]
    # Lock states:
    # - false: no lock
    # - true: closed lock, not evaluating new connections
    # - n (int in [1, infinity)): after k = n active connections, controller will not
    # accept new connections until k < n
    lock: Optional[Lock]


class DisplaySettingsMessage(BaseMessage):
    settings: DisplaySettings
    type = MessageType.DISPLAY_SETTINGS


class LifecycleMessage(BaseMessage, AppClientIdentifiableMixin):
    paused: bool
    type = MessageType.LIFECYCLE


message_type_map: Dict[MessageType, Type[BaseMessage]] = {
    MessageType.HEARTBEAT_APP: HeartbeatAppMessage,
    MessageType.HEARTBEAT_CLIENT: HeartbeatClientMessage,
    MessageType.CONNECT: ConnectMessage,
    MessageType.ACCESS: AccessMessage,
    MessageType.APPLICATION_CLIENT: ApplicationClientMessage,
    MessageType.APPLICATION_APP: ApplicationAppMessage,
    MessageType.ERROR: ErrorMessage,
    MessageType.DISPLAY_SETTINGS: DisplaySettingsMessage,
    MessageType.LIFECYCLE: LifecycleMessage,
}


def serialize(data: BaseMessage) -> JsonDict:
    return data.dict(exclude_none=True)


def deserialize(data: JsonDict) -> BaseMessage:
    if FIELD_MSG_TYPE not in data:
        raise InvalidMessageSchemaError(
            f"Message doesn't contain required field '{FIELD_MSG_TYPE}'"
        )

    if not isinstance(data[FIELD_MSG_TYPE], MessageType):
        data[FIELD_MSG_TYPE] = MessageType(data[FIELD_MSG_TYPE])

    msg_type: MessageType = data[FIELD_MSG_TYPE]
    if msg_type not in message_type_map:
        raise UnknownMessageTypeError(
            f"Message type '{msg_type.value}' is unrecognized"
        )

    return message_type_map[msg_type](**data)

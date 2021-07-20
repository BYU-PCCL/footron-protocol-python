# TODO: Use Pydantic instead of dataclasses here
from __future__ import annotations

import dataclasses
import enum
from typing import Type, Optional, Any, Dict, TypedDict, Union, List

from .errors import *

PROTOCOL_VERSION = 1
FIELD_MSG_TYPE = "type"

JsonDict = Dict[str, Union[Any, Any]]


@enum.unique
class MessageType(enum.Enum):

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


@dataclasses.dataclass
class BaseMessage:
    version: int
    type: MessageType

    @classmethod
    def create(cls, **kwargs) -> BaseMessage:
        # Force using class defined type
        if "type" in kwargs:
            del kwargs["type"]
        # noinspection PyArgumentList
        return cls(type=cls.type, version=PROTOCOL_VERSION, **kwargs)


@dataclasses.dataclass
class ClientBoundMixin:
    """A message bound for a client connection.

    Note that the app to which messages sent by a client are bound is specified by the client connection request and the
    associated access response. The client has no other control over which app is the recipient of its messages.
    """

    client: str
    app: str


@dataclasses.dataclass
class HeartbeatMessage(BaseMessage, ClientBoundMixin):
    up: bool
    type = MessageType.HEARTBEAT_APP


@dataclasses.dataclass
class ClientHeartbeatMessage(HeartbeatMessage):
    clients: List[str]
    type = MessageType.HEARTBEAT_CLIENT


@dataclasses.dataclass
class ConnectMessage(BaseMessage):
    app: str
    type = MessageType.CONNECT


@dataclasses.dataclass
class AccessMessage(BaseMessage):
    accepted: bool
    # Note that we don't use ClientBoundMixin here. This is because access can be denied by the router before a
    # client has a chance to request an app connection--like if a client is using an outdated auth code--making the
    # 'app' field null. The reverse is not true; e.g., an access message can't be sent to _accept_ a connection without
    # providing a value for 'app'.
    client: Optional[str] = None
    app: Optional[str] = None
    reason: Optional[str] = None
    type = MessageType.ACCESS


@dataclasses.dataclass
class BaseApplicationMessage(BaseMessage):
    body: Any
    #: Request ID
    req: Optional[str] = None


@dataclasses.dataclass
class ApplicationClientMessage(BaseApplicationMessage):
    type = MessageType.APPLICATION_CLIENT


@dataclasses.dataclass
class ApplicationAppMessage(BaseApplicationMessage, ClientBoundMixin):
    type = MessageType.APPLICATION_APP


@dataclasses.dataclass
class ErrorMessage(BaseMessage):
    error: str
    type = MessageType.ERROR


class DisplaySettings(TypedDict):
    end_time: int
    # Lock states:
    # - false: no lock
    # - true: closed lock, not evaluating new connections
    # - n (int in [1, infinity)): after k = n active connections, controller will not accept new connections until k < n
    lock: Union[bool, int]


@dataclasses.dataclass
class DisplaySettingsMessage(BaseMessage):
    settings: DisplaySettings
    type = MessageType.DISPLAY_SETTINGS


@dataclasses.dataclass
class LifecycleMessage(BaseMessage):
    paused: bool
    type = MessageType.LIFECYCLE


message_type_map: Dict[MessageType, Type[BaseMessage]] = {
    MessageType.HEARTBEAT_APP: HeartbeatMessage,
    MessageType.HEARTBEAT_CLIENT: ClientHeartbeatMessage,
    MessageType.CONNECT: ConnectMessage,
    MessageType.ACCESS: AccessMessage,
    MessageType.APPLICATION_CLIENT: ApplicationClientMessage,
    MessageType.APPLICATION_APP: ApplicationAppMessage,
    MessageType.ERROR: ErrorMessage,
    MessageType.DISPLAY_SETTINGS: DisplaySettingsMessage,
    MessageType.LIFECYCLE: LifecycleMessage,
}


def serialize(data: BaseMessage) -> JsonDict:
    # TODO: If we end up needing to profile this code, we might want to use .__dict__() here instead:
    #  https://stackoverflow.com/questions/52229521/why-is-dataclasses-asdictobj-10x-slower-than-obj-dict

    # This is a very hacky way (likely with better alternatives) to just get the 'type' field as its primitive type
    return {**dataclasses.asdict(data), "type": data.type.value}


def deserialize(data: JsonDict) -> BaseMessage:
    if FIELD_MSG_TYPE not in data:
        raise InvalidMessageSchemaError(
            f"Message doesn't contain required field '{FIELD_MSG_TYPE}'"
        )

    data[FIELD_MSG_TYPE] = MessageType(data[FIELD_MSG_TYPE])

    msg_type = data[FIELD_MSG_TYPE]
    if msg_type not in message_type_map:
        raise UnknownMessageTypeError(
            f"Message type '{msg_type.value}' is unrecognized"
        )

    return message_type_map[msg_type].create(**data)

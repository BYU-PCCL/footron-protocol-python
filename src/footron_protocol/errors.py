class ProtocolError(Exception):
    """Base for all protocol errors"""

    pass


class AccessError(ProtocolError):
    """A unauthorized client attempted to send an authenticated message"""

    pass


class UnknownMessageTypeError(ProtocolError):
    """A client or app sent a readable message with an unregistered type"""

    pass


class InvalidMessageSchemaError(ProtocolError):
    """A client or app sent a message with an incorrect schema"""

    pass


class UnhandledMessageTypeError(ProtocolError):
    """A client or app sent a valid message type that couldn't be handled"""

    pass

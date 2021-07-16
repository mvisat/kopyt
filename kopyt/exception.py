"""Module for all exceptions related to Kopyt package."""


class KopytException(Exception):
    """Base class for all Kopyt exceptions."""
    pass


class LexerException(KopytException):
    pass


class ParserException(KopytException):
    pass

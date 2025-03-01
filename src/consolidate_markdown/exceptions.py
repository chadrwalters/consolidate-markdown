"""Exceptions used by the consolidate_markdown package."""


class ProcessorError(Exception):
    """Base class for processor-related errors."""

    pass


class ConfigurationError(ProcessorError):
    """Error related to configuration issues."""

    pass


class APIError(ProcessorError):
    """Error related to API calls (OpenAI, Anthropic, etc.)."""

    pass


class AttachmentError(ProcessorError):
    """Error related to attachment processing."""

    pass


class CacheError(ProcessorError):
    """Error related to cache operations."""

    pass


class DependencyError(ProcessorError):
    """Error related to missing external dependencies."""

    pass


class FileSystemError(ProcessorError):
    """Error related to file system operations."""

    pass


class FormatError(ProcessorError):
    """Error related to file format issues."""

    pass


class NetworkError(ProcessorError):
    """Error related to network operations."""

    pass

"""Unit tests for exceptions module."""

import pytest

from consolidate_markdown.exceptions import ProcessorError


def test_processor_error_creation():
    """Test that ProcessorError can be created with a message."""
    error = ProcessorError("Test error message")
    assert isinstance(error, ProcessorError)
    assert str(error) == "Test error message"


def test_processor_error_inheritance():
    """Test that ProcessorError inherits from Exception."""
    error = ProcessorError("Test error")
    assert isinstance(error, Exception)


def test_processor_error_raising():
    """Test that ProcessorError can be raised and caught."""
    with pytest.raises(ProcessorError) as excinfo:
        raise ProcessorError("Test raising error")

    assert "Test raising error" in str(excinfo.value)


def test_processor_error_with_nested_exception():
    """Test ProcessorError with a nested exception."""
    try:
        raise ValueError("Original error")
    except ValueError as e:
        error = ProcessorError(f"Wrapped error: {str(e)}")

    assert "Wrapped error: Original error" in str(error)

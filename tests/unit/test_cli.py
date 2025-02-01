"""Test CLI argument parsing."""

from pathlib import Path

import pytest

from consolidate_markdown.__main__ import parse_args


def test_default_args(monkeypatch):
    """Test default argument values."""
    monkeypatch.setattr("sys.argv", ["consolidate-markdown"])
    args = parse_args()
    assert args.config == Path("config.toml")
    assert not args.no_image
    assert not args.force
    assert not args.delete
    assert args.log_level == "INFO"
    assert args.processor is None
    assert args.limit is None


def test_processor_arg(monkeypatch):
    """Test processor argument."""
    monkeypatch.setattr("sys.argv", ["consolidate-markdown", "--processor", "bear"])
    args = parse_args()
    assert args.processor == "bear"


def test_invalid_processor(monkeypatch):
    """Test invalid processor argument."""
    with pytest.raises(SystemExit):
        monkeypatch.setattr(
            "sys.argv", ["consolidate-markdown", "--processor", "invalid"]
        )
        parse_args()


def test_limit_arg(monkeypatch):
    """Test limit argument."""
    monkeypatch.setattr("sys.argv", ["consolidate-markdown", "--limit", "5"])
    args = parse_args()
    assert args.limit == 5


def test_combined_args(monkeypatch):
    """Test processor and limit arguments together."""
    monkeypatch.setattr(
        "sys.argv",
        ["consolidate-markdown", "--processor", "bear", "--limit", "2"],
    )
    args = parse_args()
    assert args.processor == "bear"
    assert args.limit == 2

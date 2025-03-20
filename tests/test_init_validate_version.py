import pytest
from click import BadParameter

from kevinbotlib_deploytool.cli_init import validate_version


def test_valid_version():
    assert validate_version(None, None, "3.10", (3, 10), (4, 0)) == "3.10"
    assert validate_version(None, None, "3.9", (3, 0), (4, 0)) == "3.9"
    assert validate_version(None, None, "2.36") == "2.36"


def test_invalid_format():
    with pytest.raises(BadParameter):
        validate_version(None, None, "three.ten")


def test_below_min_version():
    with pytest.raises(BadParameter):
        validate_version(None, None, "3.9", (3, 10), (4, 0))


def test_above_max_version():
    with pytest.raises(BadParameter):
        validate_version(None, None, "4.0", (3, 10), (4, 0))


def test_negative_version():
    with pytest.raises(BadParameter):
        validate_version(None, None, "-3.10")
    with pytest.raises(BadParameter):
        validate_version(None, None, "3.-10")

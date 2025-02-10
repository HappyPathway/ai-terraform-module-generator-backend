import pytest
from ..validation import ModuleValidator
import zipfile

def test_validate_module_metadata():
    is_valid, errors = ModuleValidator.validate_module_metadata(
        namespace="test",
        name="module",
        provider="aws",
        version="1.0.0"
    )
    assert is_valid
    assert len(errors) == 0

def test_validate_invalid_version():
    is_valid, errors = ModuleValidator.validate_module_metadata(
        namespace="test",
        name="module",
        provider="aws",
        version="invalid"
    )
    assert not is_valid
    assert any("Version must be" in msg for msg in errors.values())

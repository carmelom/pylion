import pytest
from pathlib import Path


@pytest.fixture
def cleanup():
    yield
    p = Path("test")
    for filename in p.iterdir():
        filename.unlink()
    p.rmdir()

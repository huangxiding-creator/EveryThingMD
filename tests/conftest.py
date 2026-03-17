"""Test configuration and fixtures."""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def sample_documents(temp_dir):
    """Create sample documents for testing."""
    docs_dir = temp_dir / "documents"
    docs_dir.mkdir()

    # Create a simple text file
    txt_file = docs_dir / "sample.txt"
    txt_file.write_text("This is a sample document for testing.", encoding="utf-8")

    # Create a simple markdown file
    md_file = docs_dir / "sample.md"
    md_file.write_text("# Sample Document\n\nThis is a test.", encoding="utf-8")

    return docs_dir


@pytest.fixture
def output_dir(temp_dir):
    """Create an output directory for tests."""
    output = temp_dir / "output"
    output.mkdir()
    return output

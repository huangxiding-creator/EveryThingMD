"""Tests for DualConverter."""
import pytest
from pathlib import Path
from dir2md.dir2md_dual import (
    DualConverter,
    ConversionStats,
    SUPPORTED_EXTENSIONS,
    OCR_PREFERRED_EXTENSIONS,
)


def test_supported_extensions():
    """Test that expected extensions are supported."""
    assert ".pdf" in SUPPORTED_EXTENSIONS
    assert ".docx" in SUPPORTED_EXTENSIONS
    assert ".txt" in SUPPORTED_EXTENSIONS
    assert ".png" in SUPPORTED_EXTENSIONS


def test_ocr_preferred_extensions():
    """Test OCR preferred extensions."""
    assert ".png" in OCR_PREFERRED_EXTENSIONS
    assert ".jpg" in OCR_PREFERRED_EXTENSIONS
    assert ".jpeg" in OCR_PREFERRED_EXTENSIONS
    assert ".pdf" not in OCR_PREFERRED_EXTENSIONS


def test_conversion_stats():
    """Test ConversionStats dataclass."""
    stats = ConversionStats()
    assert stats.total_files == 0
    assert stats.converted_files == 0
    assert stats.failed_files == 0
    assert stats.tool_wins == {"markitdown": 0, "paddleocr": 0, "single_option": 0}


def test_conversion_stats_to_dict():
    """Test ConversionStats.to_dict()."""
    stats = ConversionStats(
        total_files=10,
        converted_files=8,
        failed_files=2,
        skipped_files=0,
    )

    result = stats.to_dict()

    assert result["total_files"] == 10
    assert result["converted_files"] == 8
    assert result["failed_files"] == 2
    assert "success_rate" in result


def test_converter_initialization(temp_dir, output_dir):
    """Test DualConverter initialization."""
    converter = DualConverter(
        input_dir=str(temp_dir),
        output_dir=str(output_dir),
        workers=2,
    )

    assert converter.input_dir == temp_dir
    assert converter.output_dir == output_dir
    assert converter.workers == 2


def test_converter_skip_dir(temp_dir):
    """Test directory skipping logic."""
    converter = DualConverter(
        input_dir=str(temp_dir),
        output_dir=str(temp_dir / "output"),
    )

    # Should skip hidden directories
    assert converter._should_skip_dir(Path(temp_dir / ".git")) is True
    assert converter._should_skip_dir(Path(temp_dir / "__pycache__")) is True

    # Should not skip normal directories
    assert converter._should_skip_dir(Path(temp_dir / "documents")) is False


def test_converter_output_path_preserve_structure(temp_dir, output_dir):
    """Test output path generation with structure preservation."""
    converter = DualConverter(
        input_dir=str(temp_dir),
        output_dir=str(output_dir),
        preserve_structure=True,
    )

    # Create a nested file
    nested_dir = temp_dir / "subdir"
    nested_dir.mkdir()
    test_file = nested_dir / "document.pdf"

    output_path = converter._get_output_path(test_file)

    assert output_path.name == "document.md"
    assert "subdir" in str(output_path)


def test_converter_output_path_flat(temp_dir, output_dir):
    """Test output path generation without structure preservation."""
    converter = DualConverter(
        input_dir=str(temp_dir),
        output_dir=str(output_dir),
        preserve_structure=False,
    )

    nested_dir = temp_dir / "subdir"
    nested_dir.mkdir()
    test_file = nested_dir / "document.pdf"

    output_path = converter._get_output_path(test_file)

    assert output_path.name == "document.md"
    assert output_path.parent == output_dir


def test_converter_collect_files(sample_documents, output_dir):
    """Test file collection."""
    converter = DualConverter(
        input_dir=str(sample_documents),
        output_dir=str(output_dir),
    )

    files = converter.collect_files()

    # Should find at least the txt and md files we created
    assert len(files) >= 2


def test_converter_with_extensions_filter(sample_documents, output_dir):
    """Test file collection with extension filter."""
    converter = DualConverter(
        input_dir=str(sample_documents),
        output_dir=str(output_dir),
        extensions=[".txt"],
    )

    files = converter.collect_files()

    # Should only find txt files
    for f in files:
        assert f.suffix == ".txt"


def test_converter_with_exclude_patterns(sample_documents, output_dir):
    """Test file collection with exclude patterns."""
    # Create a file that should be excluded
    exclude_file = sample_documents / "temp_file.txt"
    exclude_file.write_text("temp content", encoding="utf-8")

    converter = DualConverter(
        input_dir=str(sample_documents),
        output_dir=str(output_dir),
        exclude_patterns=["temp"],
    )

    files = converter.collect_files()

    # Should not include the temp file
    for f in files:
        assert "temp" not in f.name.lower()

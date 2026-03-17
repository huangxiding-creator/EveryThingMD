"""Tests for QualityEvaluator."""
import pytest
from pathlib import Path
from dir2md.dir2md_dual import QualityEvaluator, QualityScore


def test_quality_evaluator_empty_text(tmp_path):
    """Test evaluator with empty text."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample content", encoding="utf-8")

    evaluator = QualityEvaluator(test_file)
    score = evaluator.evaluate("")

    assert score.accuracy == 0
    assert score.completeness == 0
    assert score.weighted_score == 0


def test_quality_evaluator_normal_text(tmp_path):
    """Test evaluator with normal text."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample content" * 100, encoding="utf-8")

    evaluator = QualityEvaluator(test_file)
    text = "This is a normal sentence. 它包含中文字符。Another sentence here."
    score = evaluator.evaluate(text)

    assert score.accuracy > 0
    assert score.completeness > 0
    assert score.weighted_score > 0


def test_quality_evaluator_garbage_detection(tmp_path):
    """Test garbage character detection."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample content", encoding="utf-8")

    evaluator = QualityEvaluator(test_file)

    # Text with control characters should have lower accuracy
    garbage_text = "Normal text with \x00\x01\x02 garbage"
    garbage_score = evaluator.evaluate(garbage_text)

    clean_text = "Normal text without garbage characters."
    clean_score = evaluator.evaluate(clean_text)

    assert clean_score.accuracy > garbage_score.accuracy


def test_quality_score_dataclass():
    """Test QualityScore dataclass."""
    score = QualityScore(
        accuracy=80.0,
        completeness=90.0,
        weighted_score=84.0,
        details={"char_count": 100}
    )

    assert score.accuracy == 80.0
    assert score.completeness == 90.0
    assert score.weighted_score == 84.0
    assert score.details["char_count"] == 100


def test_chinese_ratio_calculation(tmp_path):
    """Test Chinese character ratio calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample", encoding="utf-8")

    evaluator = QualityEvaluator(test_file)

    # Text with Chinese characters
    chinese_text = "这是中文测试。This is English."
    ratio = evaluator._get_chinese_ratio(chinese_text)

    assert ratio > 0
    assert ratio < 1


def test_garbage_ratio_calculation(tmp_path):
    """Test garbage ratio calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample", encoding="utf-8")

    evaluator = QualityEvaluator(test_file)

    # Clean text
    clean_ratio = evaluator._get_garbage_ratio("Clean text without issues")
    assert clean_ratio == 0

    # Text with replacement characters
    garbage_ratio = evaluator._get_garbage_ratio("Text with ��� replacement chars")
    assert garbage_ratio > 0

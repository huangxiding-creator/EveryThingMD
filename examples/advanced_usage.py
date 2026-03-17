#!/usr/bin/env python3
"""
Advanced usage example for EveryThingMD.

This script demonstrates advanced features like:
- Custom file filtering
- Quality evaluation
- Progress tracking
"""

import os
from pathlib import Path
from dir2md import DualConverter, QualityEvaluator

def main():
    # Example 1: Convert only PDF files
    print("📄 Example 1: Convert PDF files only")
    converter = DualConverter(
        input_dir="./documents",
        output_dir="./markdown_pdfs",
        extensions=[".pdf"],
        overwrite=True,
    )
    stats = converter.convert()
    print(f"   Converted {stats.converted_files} PDF files\n")

    # Example 2: Exclude certain patterns
    print("🚫 Example 2: Exclude temporary files")
    converter = DualConverter(
        input_dir="./documents",
        output_dir="./markdown_filtered",
        exclude_patterns=["temp", "backup", ".bak", "draft"],
    )
    stats = converter.convert()
    print(f"   Converted {stats.converted_files} files (excluding temps)\n")

    # Example 3: Prefer specific tool
    print("🔧 Example 3: Prefer PaddleOCR for scanned documents")
    converter = DualConverter(
        input_dir="./scanned_documents",
        output_dir="./markdown_ocr",
        prefer_tool="paddleocr",
    )
    stats = converter.convert()
    print(f"   Converted {stats.converted_files} files with OCR\n")

    # Example 4: Evaluate text quality manually
    print("📊 Example 4: Evaluate text quality")
    sample_file = Path("./documents/sample.pdf")
    if sample_file.exists():
        evaluator = QualityEvaluator(sample_file)
        sample_text = "This is a sample text for quality evaluation."
        score = evaluator.evaluate(sample_text)
        print(f"   Accuracy: {score.accuracy:.1f}")
        print(f"   Completeness: {score.completeness:.1f}")
        print(f"   Weighted Score: {score.weighted_score:.1f}\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Basic usage example for EveryThingMD.

This script demonstrates how to use the Python API to convert documents.
"""

from dir2md import DualConverter

def main():
    # Initialize the converter
    converter = DualConverter(
        input_dir="./documents",
        output_dir="./markdown_output",
        workers=4,
        verbose=True,
    )

    # Run the conversion
    stats = converter.convert()

    # Print results
    print(f"\n✅ Conversion complete!")
    print(f"   Total files: {stats.total_files}")
    print(f"   Converted: {stats.converted_files}")
    print(f"   Failed: {stats.failed_files}")
    print(f"   Time: {stats.total_time:.2f}s")

    # Show tool statistics
    print(f"\n📊 Tool Statistics:")
    print(f"   MarkItDown wins: {stats.tool_wins['markitdown']}")
    print(f"   PaddleOCR wins: {stats.tool_wins['paddleocr']}")

if __name__ == "__main__":
    main()

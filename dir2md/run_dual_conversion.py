#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper script to run dual-tool conversion"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dir2md_dual import DualConverter

def main():
    input_dir = r"e:\CPOPC\EveryThingMD\《中国风电工程EPC总承包发展研究报告》"
    output_dir = r"e:\CPOPC\EveryThingMD\《中国风电工程EPC总承包发展研究报告》_md_v3"

    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")

    converter = DualConverter(
        input_dir=input_dir,
        output_dir=output_dir,
        workers=1,  # Single worker to reduce memory usage
        overwrite=False,  # Don't overwrite existing files
        verbose=True
    )

    stats = converter.convert()

    print("\n" + "="*60)
    print("Conversion Complete!")
    print(f"Total files: {stats.total_files}")
    print(f"Converted: {stats.converted_files}")
    print(f"Skipped (existing): {stats.skipped_files}")
    print(f"Failed: {stats.failed_files}")
    print(f"Total time: {stats.total_time:.1f} seconds")
    print(f"Tool wins: {stats.tool_wins}")

    if stats.errors:
        print("\nErrors:")
        for path, error in stats.errors:
            print(f"  - {path}: {error}")

if __name__ == "__main__":
    main()

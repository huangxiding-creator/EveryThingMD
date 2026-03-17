"""
EveryThingMD - AI-Powered Document to Markdown Converter

Intelligent dual-engine conversion with quality comparison & auto-selection.
"""

__version__ = "1.0.0"
__author__ = "huangxiding-creator"

from dir2md.dir2md_dual import (
    DualConverter,
    QualityEvaluator,
    QualityScore,
    ConversionResult,
    ConversionStats,
    SUPPORTED_EXTENSIONS,
    OCR_PREFERRED_EXTENSIONS,
)

__all__ = [
    "DualConverter",
    "QualityEvaluator",
    "QualityScore",
    "ConversionResult",
    "ConversionStats",
    "SUPPORTED_EXTENSIONS",
    "OCR_PREFERRED_EXTENSIONS",
    "__version__",
    "__author__",
]

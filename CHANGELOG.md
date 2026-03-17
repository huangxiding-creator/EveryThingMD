# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-17

### Added
- 🎉 Initial release
- **Dual-Engine Conversion**: Intelligent comparison between MarkItDown and PaddleOCR
- **Quality Scoring System**: Accuracy (60%) + Completeness (40%) weighted evaluation
- **50+ Format Support**: PDF, Word, Excel, PPT, EPUB, Images, Audio, ZIP
- **Smart Optimization**: Auto-skips OCR for PDFs > 20 pages
- **Image OCR**: Extract text from images using PaddleOCR
- **CLI Interface**: Easy-to-use command line tool
- **Python API**: Programmatic access to all features
- **Conversion Reports**: JSON reports with detailed statistics
- **Parallel Processing**: Multi-threaded conversion for better performance

### Features
- MarkItDown integration for digital document parsing
- PaddleOCR integration for scanned documents and images
- Automatic quality comparison and best result selection
- Preserves directory structure during conversion
- Detailed logging and progress tracking

### Technical Details
- Python 3.8+ support
- Type hints throughout codebase
- Comprehensive error handling
- Modular architecture for extensibility

## [Unreleased]

### Planned
- 🌐 Web UI with drag & drop
- 🔌 VS Code Extension
- 📱 Mobile app support
- 🤖 LLM integration (auto-summarization)
- 🔄 Real-time collaboration
- 📊 Batch quality reports
- 🎨 Custom output templates

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-03-17 | Initial release with dual-engine conversion |

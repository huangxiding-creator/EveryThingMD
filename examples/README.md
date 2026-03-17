# Examples

This directory contains example scripts demonstrating how to use EveryThingMD.

## Basic Usage

```bash
python basic_usage.py
```

Demonstrates the simplest way to convert documents using the Python API.

## Advanced Usage

```bash
python advanced_usage.py
```

Shows advanced features including:
- Custom file filtering by extension
- Excluding patterns
- Preferring specific conversion tools
- Manual quality evaluation

## Command Line Examples

```bash
# Basic conversion
everythingmd ./documents -o ./markdown

# Verbose output
everythingmd ./documents -v

# Convert only PDF and Word files
everythingmd ./documents -e .pdf .docx .doc

# Exclude temporary files
everythingmd ./documents --exclude "temp" "backup"

# Prefer MarkItDown for all formats
everythingmd ./documents --prefer markitdown

# Force overwrite existing files
everythingmd ./documents --overwrite
```

## Docker Examples

```bash
# Build the Docker image
docker build -t everythingmd .

# Run conversion with Docker
docker run -v $(pwd)/documents:/input -v $(pwd)/output:/output everythingmd

# Run with custom options
docker run -v $(pwd)/documents:/input -v $(pwd)/output:/output everythingmd /input -o /output -v
```

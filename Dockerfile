FROM python:3.11-slim

LABEL maintainer="huangxiding-creator"
LABEL description="EveryThingMD - AI-Powered Document to Markdown Converter"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package files
COPY pyproject.toml .
COPY dir2md/ ./dir2md/

# Install the package
RUN pip install --no-cache-dir -e .

# Create input/output directories
RUN mkdir -p /input /output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
ENTRYPOINT ["everythingmd"]
CMD ["/input", "-o", "/output"]

# PDF Library

A Python application that automatically collects, processes, and stores health-related PDF documents with AI-powered metadata extraction.

## Overview

This project downloads health-related PDFs from academic sources, extracts text content, and uses AI to generate structured metadata including title, summary, tags, publication year, organization, country, and language.

## Features

- **PDF Collection**: Automatically downloads health-related PDFs from OpenAlex API
- **Text Extraction**: Parses PDF content to extract readable text
- **AI Metadata Extraction**: Uses AI to generate structured metadata from PDF content
- **Database Storage**: Stores metadata and file paths in PostgreSQL database
- **Concurrent Processing**: Multi-threaded processing for efficient PDF handling

## Project Structure

```
pdf_library/
├── src/
│   ├── ai/                 # AI metadata extraction
│   ├── database/           # PostgreSQL client
│   ├── download/           # PDF downloading and collection
│   ├── parsers/            # PDF text parsing
│   ├── utils/              # Configuration utilities
│   └── main.py            # Main application entry point
├── data/
│   └── raw/               # Downloaded PDF files
├── config.yaml            # Configuration settings
└── requirements.txt       # Python dependencies
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure database connection with env variables

3. Run the application:
   ```bash
   python src/main.py
   ```

## Configuration

The `config.yaml` file contains:
- AI prompts for metadata extraction
- OpenAlex API configuration for PDF discovery
- Response key definitions

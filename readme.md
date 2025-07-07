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

## Database Table Structure

### `pdf_metadata`
Stores extracted metadata for each processed PDF.

| Column           | Type            | Description                                 |
|------------------|-----------------|---------------------------------------------|
| id               | serial PRIMARY KEY | Auto-incrementing unique row identifier     |
| title            | text            | Title of the document                       |
| summary          | text            | Summary of the document                     |
| tags             | array           | List of tags (topics/keywords)              |
| year_published   | text            | Year of publication                         |
| organization     | text            | Publishing organization                     |
| country          | text            | Country of origin                           |
| language         | text            | Language of the document                    |
| pdf_path         | text            | Local file path to the downloaded PDF       |

### `download_logs`
Logs each PDF download attempt.

| Column         | Type            | Description                                 |
|----------------|-----------------|---------------------------------------------|
| id             | serial PRIMARY KEY | Auto-incrementing unique row identifier     |
| url            | text            | Source URL of the PDF                       |
| local_path     | text            | Local file path (if downloaded)             |
| status         | text            | Download status (success, error, etc.)      |
| error_message  | text            | Error message if download failed            |
| duration_sec   | float           | Download duration in seconds                |
| timestamp      | text            | Download timestamp                          |

### `extraction_logs`
Logs each AI metadata extraction attempt.

| Column         | Type            | Description                                 |
|----------------|-----------------|---------------------------------------------|
| id             | serial PRIMARY KEY | Auto-incrementing unique row identifier     |
| sys_prompt     | text            | System prompt used for extraction           |
| prompt         | text            | User prompt used for extraction             |
| response       | text            | Raw AI response                             |
| status         | text            | Extraction status (success, error, etc.)    |
| error_message  | text            | Error message if extraction failed          |
| duration_sec   | float           | Extraction duration in seconds              |
| timestamp      | text            | Extraction timestamp                        |

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
